import re

GUIDE_FIELD_NAMES = (
    "TITLE",
    "AUDIENCE",
    "TAGS",
    "CONTEXT",
    "STEPS",
    "IF NOT FIXED",
    "ESCALATE",
)

GUIDE_FIELD_PATTERN = re.compile(
    r"^\s*-\s*(TITLE|AUDIENCE|TAGS|CONTEXT|STEPS|IF NOT FIXED|ESCALATE):\s*(.*)$",
    flags=re.IGNORECASE,
)

GUIDE_METADATA_LABELS = {
    "title:",
    "audience:",
    "tags:",
    "context:",
    "steps:",
    "if not fixed:",
    "escalate:",
}


def build_tone_profile(question=None, source_name=None):
    """
    Return concise, consistent guided-response tone copy.
    """
    lowered_question = (question or "").lower()
    profile = {
        "steps_label": "Try these steps",
        "followup_label": "If that didn’t work",
        "escalation_label": "Still stuck? Contact IT Support",
        "guided_intro": "Here's what to try.",
        "steps_note": "Try these steps in order.",
        "followup_note": "If that didn't work, try these next steps.",
        "escalation_intro": "No worries — IT Support can help you if the issue is still not resolved.",
    }

    if "wifi" in lowered_question or "wireless" in lowered_question:
        profile.update(
            {
                "guided_intro": "Let's get you connected.",
                "steps_note": "This is a common issue. Try these steps in order.",
                "followup_note": "If that didn't work, try these next checks.",
                "escalation_intro": "No worries — IT Support can help you if the connection still is not working.",
            }
        )
        return profile

    if "password" in lowered_question or "account" in lowered_question or source_name == "password-reset.txt":
        profile.update(
            {
                "guided_intro": "Let's get this working.",
                "steps_note": "Usually this fixes it. Try these steps in order.",
                "followup_note": "If that didn't work, these next checks usually help narrow it down.",
                "escalation_intro": "No worries — IT Support can help if sign-in is still blocked.",
            }
        )
        return profile

    if "print" in lowered_question:
        profile["guided_intro"] = "Here's what to try."
        return profile

    if "zoom" in lowered_question or "d2l" in lowered_question or "email" in lowered_question:
        profile["guided_intro"] = "Let's get this working."
        return profile

    return profile


def is_heading_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("-", "•")):
        return False
    if stripped.endswith(":"):
        return True
    return stripped.isupper() and len(stripped.split()) <= 8


def is_guide_field_line(line):
    return bool(GUIDE_FIELD_PATTERN.match(line or ""))


def is_guide_metadata_line(line):
    stripped = (line or "").strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if lowered == "guide ready fields:":
        return True
    if lowered in GUIDE_METADATA_LABELS:
        return True
    if lowered.startswith("- "):
        candidate = lowered[2:]
        if candidate in GUIDE_METADATA_LABELS:
            return True
    return bool(GUIDE_FIELD_PATTERN.match(stripped))


def strip_guide_metadata_lines(text):
    """
    Remove guide field labels and metadata lines from resolved guide content.
    """
    if not text:
        return ""

    cleaned_lines = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if is_guide_metadata_line(stripped):
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines).strip()


def count_user_facing_steps(text):
    """
    Count non-metadata user-facing step lines in a block of text.
    """
    cleaned = strip_guide_metadata_lines(text)
    if not cleaned:
        return 0
    count = 0
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if is_guide_metadata_line(stripped):
            continue
        count += 1
    return count


def parse_section_map(content_text):
    """
    Build a simple heading -> body map for one document.
    """
    if not content_text or not content_text.strip():
        return {}

    section_map = {}
    current_heading = None
    current_lines = []

    for raw_line in content_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if is_guide_field_line(stripped):
            break
        if stripped.lower() == "guide ready fields:":
            break
        if stripped.startswith("SOURCE:") or set(stripped) <= {"=", "-", "`"}:
            continue

        if is_heading_line(stripped):
            if current_heading and current_lines:
                section_map[current_heading] = "\n".join(current_lines).strip()
            current_heading = stripped
            current_lines = []
            continue

        if current_heading:
            current_lines.append(stripped)

    if current_heading and current_lines:
        section_map[current_heading] = "\n".join(current_lines).strip()

    return section_map


def parse_guide_content(content_text):
    """
    Parse optional guide-ready fields from article content.
    Expected bullet format:
    - TITLE: ...
    - AUDIENCE: ...
    - TAGS: ...
    - CONTEXT:
      - ...
    - STEPS:
      1. ...
    - IF NOT FIXED:
      - ...
    - ESCALATE:
      - ...
    """
    if not content_text or not content_text.strip():
        return {}

    parsed = {}
    current_field = None

    for raw_line in content_text.splitlines():
        line = raw_line.rstrip()
        field_match = GUIDE_FIELD_PATTERN.match(line)
        if field_match:
            current_field = field_match.group(1).upper()
            value = field_match.group(2).strip()

            if current_field in {"TITLE", "AUDIENCE", "TAGS"}:
                parsed[current_field] = value
            else:
                parsed[current_field] = []
                if value:
                    parsed[current_field].append(value)
            continue

        if not current_field:
            continue

        list_item_match = re.match(r"^\s*(?:-|\d+\.)\s+(.*)$", line)
        if list_item_match:
            value = list_item_match.group(1).strip()
            if not value:
                continue
            if current_field in {"TITLE", "AUDIENCE", "TAGS"}:
                existing = parsed.get(current_field, "")
                parsed[current_field] = f"{existing} {value}".strip()
            else:
                parsed.setdefault(current_field, []).append(value)
            continue

        stripped = line.strip()
        if not stripped:
            continue

        if current_field in {"TITLE", "AUDIENCE", "TAGS"}:
            existing = parsed.get(current_field, "")
            parsed[current_field] = f"{existing} {stripped}".strip()
        else:
            parsed.setdefault(current_field, [])
            if parsed[current_field]:
                parsed[current_field][-1] = f"{parsed[current_field][-1]} {stripped}".strip()
            else:
                parsed[current_field].append(stripped)

    if parsed.get("TAGS"):
        parsed["TAGS"] = [tag.strip() for tag in parsed["TAGS"].split(",") if tag.strip()]

    return parsed


def resolve_guide_items(items, content_text):
    """
    Resolve guide items that reference existing section headings.
    """
    if not items:
        return []

    section_map = parse_section_map(content_text)
    resolved = []
    for item in items:
        reference = item.strip()
        if reference in section_map:
            cleaned = strip_guide_metadata_lines(section_map[reference])
            if cleaned:
                resolved.append(cleaned)
        else:
            cleaned = strip_guide_metadata_lines(reference)
            if cleaned:
                resolved.append(cleaned)
    return resolved


def extract_first_url(content_text):
    """
    Return the first URL found in documentation text, if any.
    """
    if not content_text:
        return None

    match = re.search(r"https?://[^\s<>\"]+", content_text)
    if not match:
        return None

    return match.group(0).rstrip(".,);")


def extract_escalation_text(content_text):
    """
    Return explicit escalation lines from documentation, if any.
    """
    if not content_text:
        return None

    guide_content = parse_guide_content(content_text)
    if guide_content.get("ESCALATE"):
        escalation = "\n".join(resolve_guide_items(guide_content["ESCALATE"], content_text))
        escalation = strip_guide_metadata_lines(escalation)
        if escalation:
            return escalation
        return None

    escalation_lines = []
    for line in content_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            continue
        if (
            "contact it" in lowered
            or "contact the it help desk" in lowered
            or "contact the it helpdesk" in lowered
            or "please contact it support" in lowered
        ):
            escalation_lines.append(stripped)

    if not escalation_lines:
        return None

    return "\n".join(escalation_lines)


def format_source_name(source_name):
    """
    Convert internal article filenames into user-friendly titles.
    """
    if not source_name:
        return None

    cleaned_name = source_name.removesuffix(".txt").replace("-", " ").replace("_", " ").strip()
    if not cleaned_name:
        return None

    return cleaned_name.title()


def split_first_sentence(text):
    """
    Split the first sentence from the remainder for light emphasis.
    """
    if not text:
        return "", ""

    match = re.match(r"(.+?[.!?])(\s+.*)?$", text.strip(), flags=re.DOTALL)
    if not match:
        return text.strip(), ""

    first = match.group(1).strip()
    rest = (match.group(2) or "").strip()
    return first, rest


def build_response_blocks(answer_text):
    """
    Convert plain answer text into paragraphs and numbered-step blocks for rendering.
    """
    if not answer_text or not answer_text.strip():
        return []

    blocks = []
    paragraphs = [part.strip() for part in answer_text.split("\n\n") if part.strip()]

    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        numbered_lines = []
        bullet_lines = []
        for line in lines:
            match = re.match(r"^\d+\.\s+(.*)$", line)
            bullet_match = re.match(r"^[-•]\s+(.*)$", line)
            if match:
                numbered_lines.append(match.group(1).strip())
                continue
            if bullet_match:
                bullet_lines.append(bullet_match.group(1).strip())
                continue
            numbered_lines = []
            bullet_lines = []
            break

        if numbered_lines:
            blocks.append({"type": "steps", "items": numbered_lines})
            continue

        if bullet_lines:
            blocks.append({"type": "bullets", "items": bullet_lines})
            continue

        first_sentence, remainder = split_first_sentence(paragraph)
        blocks.append(
            {
                "type": "paragraph",
                "lead": first_sentence,
                "remainder": remainder,
            }
        )

    return blocks


def detect_disambiguation_options(question):
    """
    Return workflow options for broad, ambiguous support questions.
    """
    if not question:
        return []

    normalized = " ".join(question.lower().split())
    login_phrases = (
        "can't log in",
        "cannot log in",
        "cant log in",
        "can't login",
        "cannot login",
        "cant login",
        "login issue",
        "log in help",
        "sign in help",
        "can't sign in",
        "cannot sign in",
        "problem with login",
    )
    access_phrases = (
        "can't access",
        "cannot access",
        "cant access",
        "can't open",
        "cannot open",
        "cant open",
        "issue with class",
    )
    not_working_phrases = (
        "not working",
        "nothing is working",
    )
    specific_terms = (
        "d2l",
        "brightspace",
        "email",
        "outlook",
        "account",
        "mycca",
        "password",
        "wifi",
        "zoom",
        "yuja",
        "video",
        "videos",
        "course video",
        "course videos",
        "classroom",
        "projector",
        "display",
        "audio",
        "av",
    )

    if any(term in normalized for term in specific_terms):
        return []

    if any(phrase in normalized for phrase in login_phrases):
        return [
            {"label": "D2L", "query": "I cannot log into D2L"},
            {"label": "Email", "query": "I cannot log into Outlook"},
            {"label": "Account", "query": "My MyCCA account login is not working"},
        ]

    if normalized in {"can't open anything", "cannot open anything", "cant open anything"}:
        return [
            {"label": "D2L", "query": "I cannot access D2L"},
            {"label": "Email", "query": "I cannot access my student email"},
            {"label": "Zoom", "query": "I cannot access Zoom for class"},
            {"label": "Course videos", "query": "I cannot access YuJa videos in my course"},
            {
                "label": "I'm not sure",
                "query": "I need help finding the right IT support option",
            },
        ]

    if any(phrase in normalized for phrase in access_phrases):
        return [
            {"label": "D2L", "query": "I cannot access D2L"},
            {"label": "Email", "query": "I cannot access my student email"},
            {"label": "Zoom", "query": "I cannot access Zoom for class"},
            {"label": "Course videos", "query": "I cannot access YuJa videos in my course"},
        ]

    if any(phrase in normalized for phrase in not_working_phrases):
        return [
            {"label": "Wi-Fi", "query": "Wi-Fi is not working"},
            {"label": "D2L", "query": "D2L is not working"},
            {"label": "Email", "query": "Student email is not working"},
            {"label": "Zoom", "query": "Zoom is not working"},
            {
                "label": "I'm not sure",
                "query": "I need help finding the right IT support option",
            },
        ]

    return []


def build_guided_context(question, section_heading=None, source_name=None, content_text=None):
    """
    Build a short context line for the guided procedure view.
    """
    guide_content = parse_guide_content(content_text)
    if guide_content.get("CONTEXT"):
        return " ".join(resolve_guide_items(guide_content["CONTEXT"], content_text))
    if question and section_heading:
        return f"This procedure is intended to help with: {question.strip()} It is based on the matched section '{section_heading}'."
    if question:
        return f"This procedure is intended to help with: {question.strip()}"
    if source_name:
        return f"This procedure is based on the matched documentation in {format_source_name(source_name)}."
    return "Use the documented steps below for this issue."


def heuristic_extract_step_items(answer_text):
    """
    Convert answer text into a stable list of numbered troubleshooting steps.
    """
    if not answer_text or not answer_text.strip():
        return []

    items = []
    paragraphs = [part.strip() for part in answer_text.split("\n\n") if part.strip()]
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        for line in lines:
            if is_guide_metadata_line(line):
                continue
            numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
            bullet_match = re.match(r"^[-•]\s+(.*)$", line)
            if numbered_match:
                items.append(numbered_match.group(1).strip())
                continue
            if bullet_match:
                items.append(bullet_match.group(1).strip())
                continue

        if items:
            continue

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
            if sentence.strip() and not is_guide_metadata_line(sentence.strip())
        ]
        items.extend(sentences)

    cleaned = []
    seen = set()
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)

    return cleaned


def extract_step_items(answer_text, content_text=None, question=None, section_heading=None):
    """
    Prefer structured STEPS data when available, else fall back to heuristic extraction.
    """
    lowered_question = (question or "").lower()
    lowered_heading = (section_heading or "").lower()
    direct_section_query = (
        lowered_question.startswith("where ")
        or lowered_question.startswith("who ")
        or "where do i" in lowered_question
        or "where is" in lowered_question
        or "who can help" in lowered_question
        or "who do i contact" in lowered_question
        or "who can" in lowered_question
        or "location" in lowered_question
        or "where to get help" in lowered_heading
        or "when to contact" in lowered_heading
        or "location" in lowered_heading
    )

    if direct_section_query:
        direct_steps = heuristic_extract_step_items(answer_text)
        if direct_steps:
            return direct_steps

    section_map = parse_section_map(content_text)
    if section_heading and section_heading in section_map:
        matched_section_steps = heuristic_extract_step_items(section_map[section_heading])
        if len(matched_section_steps) >= 2:
            return matched_section_steps

    guide_content = parse_guide_content(content_text)
    if guide_content.get("STEPS"):
        if section_heading and section_heading in set(guide_content.get("STEPS", [])):
            matched_steps = resolve_guide_items([section_heading], content_text)
            steps = []
            for resolved in matched_steps:
                steps.extend(heuristic_extract_step_items(resolved))
            if len(steps) >= 2:
                return steps

        steps = []
        for resolved in resolve_guide_items(guide_content["STEPS"], content_text):
            extracted = heuristic_extract_step_items(resolved)
            if extracted:
                steps.extend(extracted)
            elif resolved:
                steps.append(resolved)

        cleaned = []
        seen = set()
        for step in steps:
            key = step.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(step)
        if cleaned:
            return cleaned

    return heuristic_extract_step_items(answer_text)


def build_additional_troubleshooting_steps(question, source_name=None, content_text=None):
    """
    Provide simple next-step guidance when the first procedure did not resolve the issue.
    """
    guide_content = parse_guide_content(content_text)
    if guide_content.get("IF NOT FIXED"):
        steps = []
        for resolved in resolve_guide_items(guide_content["IF NOT FIXED"], content_text):
            extracted = heuristic_extract_step_items(resolved)
            if extracted:
                steps.extend(extracted)
            elif resolved:
                steps.append(resolved)
        if steps:
            return steps

    steps = [
        "Confirm the exact system, room, device, or account involved before trying the procedure again.",
        "Retry the procedure from the beginning and note any error message, screen, or step where the process fails.",
        "Search again using the product name and the error detail so the procedure can be narrowed to a more specific workflow.",
    ]

    question_text = (question or "").lower()
    if "wifi" in question_text or "wireless" in question_text:
        steps[1] = "Retry the connection after reconnecting to the wireless network and note whether the issue is a login failure, no internet access, or an unstable signal."
    elif "display" in question_text or "av" in question_text or "extron" in question_text:
        steps[1] = "Retry the procedure while confirming the room, display input, cable path, and control panel state so the issue can be narrowed before escalation."
    elif source_name == "password-reset.txt":
        steps[1] = "Retry the sign-in after completing the documented reset steps and note whether the issue is a password failure, account lock, or MFA prompt."

    return steps
