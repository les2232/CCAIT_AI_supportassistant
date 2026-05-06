import re

from router import normalize_text, tokenize_text

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

GENERIC_SUPPORT_HEADINGS = {
    "common classroom support issues:",
    "context:",
    "summary:",
    "when to contact it:",
    "when to use it:",
    "what to include when asking for help:",
    "what to include when contacting it:",
    "what this is:",
    "what this helps with:",
    "what students use it for:",
    "things to know:",
    "what mfa affects:",
    "if that did not work:",
}

SUPPORT_TITLE_OVERRIDES = {
    "browser or cache issues": "D2L Browser or Cache Issues",
    "outlook is not loading or email won't open": "Student Email or Outlook Not Loading",
    "outlook is not loading or email won t open": "Student Email or Outlook Not Loading",
    "how to get a semester laptop": "How to Get a Semester Laptop",
}

CONTACT_QUERY_TERMS = (
    "contact",
    "helpdesk",
    "help desk",
    "phone number",
    "talk to someone",
    "submit a ticket",
)

ACTION_STARTERS = (
    "contact ",
    "approve ",
    "choose ",
    "confirm ",
    "check ",
    "click ",
    "make sure ",
    "start ",
    "restart ",
    "reconnect ",
    "retry ",
    "try ",
    "open ",
    "go to ",
    "follow ",
    "use ",
    "turn on ",
    "turn off ",
    "select ",
    "add ",
    "clear ",
    "refresh ",
    "enter ",
    "complete ",
    "agree ",
    "navigate ",
    "visit ",
    "bring ",
    "provide ",
    "search ",
    "finish ",
    "write ",
    "print ",
    "log in ",
    "sign in ",
    "tap ",
    "reseat ",
    "wait ",
    "close ",
)

ACTION_CONTAINS = (
    " make sure ",
    " try ",
    " check ",
    " confirm ",
    " reconnect ",
    " restart ",
    " select ",
    " clear ",
)

CONTACT_MARKERS = (
    "contact ",
    "it support",
    "helpdesk",
    "help desk",
    "phone:",
    " email ",
)

SYMPTOM_MARKERS = (
    "not working",
    "won’t",
    "won t",
    "cannot",
    "can't",
    "can t",
    "no signal",
    "not showing",
    "not turn on",
    "not receiving",
    "missing",
    "broken",
    "issue",
    "issues",
    "problem",
    "problems",
    "failing",
    "blocked",
    "locked",
)

INTERNAL_GUIDE_PREFIXES = (
    "this guide is used when",
    "use this guide",
    "it covers",
    "this section explains",
    "this article covers",
    "this content is for",
    "what this helps with",
    "this guide helps",
)


def build_tone_profile(question=None, source_name=None):
    """
    Return concise, consistent guided-response tone copy.
    """
    lowered_question = (question or "").lower()
    profile = {
        "steps_label": "Try these steps",
        "followup_label": "Still need help?",
        "escalation_label": "Still stuck? Contact IT Support",
        "guided_intro": "Here's what to try.",
        "steps_note": "Start with these quick checks.",
        "followup_note": "Give that a try and let me know if it worked.",
        "escalation_intro": "No worries — IT Support can help you if the issue is still not resolved.",
        "show_context": True,
    }

    if "wifi" in lowered_question or "wireless" in lowered_question:
        if any(marker in lowered_question for marker in SYMPTOM_MARKERS):
            profile["followup_label"] = "Still not working?"
        profile.update(
            {
                "guided_intro": "Let's get you connected.",
                "steps_note": "Start with these quick checks.",
                "followup_note": "Give that a try and let me know if it worked.",
                "escalation_intro": "No worries — IT Support can help you if the connection still is not working.",
            }
        )
        return profile

    if "password" in lowered_question or "account" in lowered_question or source_name == "password-reset.txt":
        profile["followup_label"] = "Still not working?"
        profile.update(
            {
                "guided_intro": "Let's get this working.",
                "steps_note": "Start with these quick checks.",
                "followup_note": "Give that a try and let me know if it worked.",
                "escalation_intro": "No worries — IT Support can help if sign-in is still blocked.",
            }
        )
        return profile

    if "print" in lowered_question:
        profile["guided_intro"] = "Here's what to try."
        return profile

    if "zoom" in lowered_question or "d2l" in lowered_question or "email" in lowered_question:
        if any(marker in lowered_question for marker in SYMPTOM_MARKERS):
            profile["followup_label"] = "Still not working?"
        profile["guided_intro"] = "Let's get this working."
        return profile

    return profile


def should_show_context(guided_context, question=None, section_heading=None):
    """
    Hide generic context text for troubleshooting-style responses.
    """
    if not guided_context:
        return False

    lowered_question = (question or "").lower()
    lowered_heading = (section_heading or "").lower()
    troubleshooting_markers = (
        "not working",
        "can't",
        "cannot",
        "won't",
        "is not loading",
        "problem",
        "issue",
        "error",
        "troubleshooting",
    )
    if any(marker in lowered_question for marker in troubleshooting_markers):
        return False
    if any(marker in lowered_heading for marker in ("cannot", "not working", "problem", "issue")):
        return False
    return True


def is_internal_guide_text(text):
    cleaned = clean_section_heading(text).strip()
    if not cleaned:
        return False
    lowered = normalize_text(cleaned)
    return any(lowered.startswith(normalize_text(prefix)) for prefix in INTERNAL_GUIDE_PREFIXES)


def is_direct_setup_query(question):
    lowered = normalize_text(question or "")
    if not lowered:
        return False

    direct_prefixes = (
        "connect to ",
        "how do i connect to ",
        "how do i access ",
        "how do i reset ",
        "how do i log into ",
        "how do i log in to ",
        "how do i sign into ",
        "how do i sign in to ",
        "how do i set up ",
        "reset my ",
        "change my password",
        "forgot my password",
        "access ",
        "log into ",
        "log in to ",
        "sign into ",
        "sign in to ",
    )
    if any(lowered.startswith(prefix) for prefix in direct_prefixes):
        return True

    return any(
        phrase in lowered
        for phrase in (
            "connect to wifi",
            "connect to wi fi",
            "connect to the internet",
            "connect to internet",
            "get online",
            "reset my password",
            "forgot my password",
            "change my password",
            "access student email",
            "log into d2l",
            "log in to d2l",
            "access d2l",
        )
    )


def classify_wifi_query_intent(question):
    """
    Return a small Wi-Fi-specific intent used only for response shaping.
    """
    lowered = normalize_text(question or "")
    if not lowered:
        return None

    has_wifi_topic = any(
        term in lowered
        for term in (
            "wifi",
            "wi fi",
            "wireless",
            "internet",
            "network",
            "cca students",
            "cca-students",
            "online",
        )
    )
    if not has_wifi_topic:
        return None

    if any(
        phrase in lowered
        for phrase in (
            "do not see",
            "don t see",
            "dont see",
            "not showing",
            "does not show",
            "doesn t show",
            "not listed",
            "not visible",
            "cannot find",
            "can t find",
            "cant find",
        )
    ):
        return "not_visible"

    if "password" in lowered or "sign into wifi" in lowered or "sign in to wifi" in lowered:
        return "password"

    if (
        ("connected" in lowered or "connects" in lowered)
        and any(
            phrase in lowered
            for phrase in (
                "websites do not load",
                "websites don t load",
                "websites dont load",
                "website does not load",
                "no internet",
                "without internet",
                "internet does not work",
                "internet doesn t work",
                "internet isnt working",
                "internet is not working",
                "online services do not load",
            )
        )
    ):
        return "connected_no_internet"

    if any(
        phrase in lowered
        for phrase in (
            "how do i connect",
            "how can i connect",
            "connect to wifi",
            "connect to wi fi",
            "connect to the internet",
            "connect to internet",
            "get online",
            "join the student wifi",
            "join student wifi",
            "what wifi",
            "which wifi",
            "wifi do students use",
            "student wifi",
        )
    ) and not any(
        phrase in lowered
        for phrase in (
            "not working",
            "is not working",
            "isnt working",
            "won t connect",
            "wont connect",
            "cannot connect",
            "can t connect",
            "cant connect",
            "keeps dropping",
            "unstable",
            "no internet",
        )
    ):
        return "setup"

    if any(
        phrase in lowered
        for phrase in (
            "not working",
            "is not working",
            "isnt working",
            "won t connect",
            "wont connect",
            "cannot connect",
            "can t connect",
            "cant connect",
            "keeps dropping",
            "unstable",
            "no internet",
            "broke",
            "broken",
        )
    ):
        return "troubleshooting"

    return None


def is_mfa_support_content(content_text):
    lowered = normalize_text(content_text or "")
    return "mfa and account security" in lowered or "multi factor authentication" in lowered


def classify_mfa_query_intent(question):
    lowered = normalize_text(question or "")
    if not lowered:
        return None
    if "alternate" in lowered or "alternative" in lowered or "add method" in lowered:
        return "alternate_method"
    if any(term in lowered for term in ("lost phone", "lost my phone", "changed phone", "changed phones", "lost access")):
        return "lost_access"
    if any(term in lowered for term in ("mfa", "authenticator")):
        return "troubleshooting"
    return None

    return None


def is_wifi_support_content(content_text):
    return "CCA-Students" in (content_text or "")


def resolve_section_steps_by_heading(content_text, heading):
    section_map = parse_section_map(content_text)
    section_text = section_map.get(heading, "")
    if not section_text:
        return []
    return filter_action_items(heuristic_extract_step_items(section_text))


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

    formatted = cleaned_name.title()
    return (
        formatted.replace(" It ", " IT ")
        .replace(" It", " IT")
        .replace("Cca", "CCA")
        .replace("D2L", "D2L")
    )


def clean_section_heading(heading):
    cleaned_heading = (heading or "").strip()
    if cleaned_heading.endswith(":"):
        cleaned_heading = cleaned_heading[:-1]
    return cleaned_heading.strip()


def heading_is_generic(heading):
    return clean_section_heading(heading).lower() + ":" in GENERIC_SUPPORT_HEADINGS


def is_probable_action_step(text):
    cleaned = clean_section_heading(text)
    if not cleaned:
        return False
    if is_internal_guide_text(cleaned):
        return False
    lowered = normalize_text(cleaned)
    if any(lowered.startswith(normalize_text(prefix).strip()) for prefix in ACTION_STARTERS):
        return True
    padded = f" {lowered} "
    return any(token in padded for token in ACTION_CONTAINS)


def is_probable_symptom_line(text):
    cleaned = clean_section_heading(text)
    if not cleaned:
        return False
    if is_internal_guide_text(cleaned):
        return False
    lowered = normalize_text(cleaned)
    if is_probable_action_step(cleaned):
        return False
    padded = f" {lowered} "
    action_like_markers = (
        " make sure ",
        " try again ",
        " trying again",
        " check ",
        " enter ",
        " complete ",
        " note whether ",
        " restart ",
        " reconnect ",
        " open ",
        " select ",
        " turn on ",
        " turn off ",
        " agree ",
        " navigate ",
    )
    if any(marker in padded for marker in action_like_markers):
        return False
    if lowered.startswith("if you ") and "," in lowered:
        _, remainder = lowered.split(",", 1)
        remainder = f" {remainder.strip()} "
        if any(marker in remainder for marker in action_like_markers):
            return False
    normalized_contact_markers = [marker for marker in (normalize_text(m) for m in CONTACT_MARKERS) if marker]
    if any(marker in lowered for marker in normalized_contact_markers):
        return False
    return any(marker in lowered for marker in [normalize_text(m) for m in SYMPTOM_MARKERS])


def dedupe_preserve_order(items):
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


def filter_action_items(items):
    return dedupe_preserve_order([item for item in items if is_probable_action_step(item)])


def filter_symptom_items(items):
    return dedupe_preserve_order([item for item in items if is_probable_symptom_line(item)])


def section_query_score(question, heading, body_text=""):
    question_tokens = {token for token in tokenize_text(question or "") if len(token) > 2}
    if not question_tokens:
        return 0
    heading_text = normalize_text(heading or "")
    body = normalize_text(body_text or "")
    score = 0
    for token in question_tokens:
        if token in heading_text:
            score += 4
        if token in body:
            score += 2
    return score


def select_best_matching_section(question, content_text=None, require_action=False, require_symptom=False):
    section_map = parse_section_map(content_text)
    best_heading = None
    best_score = 0

    for heading, body_text in section_map.items():
        extracted = heuristic_extract_step_items(body_text)
        action_items = filter_action_items(extracted)
        symptom_items = filter_symptom_items(extracted)
        if require_action and not action_items:
            continue
        if require_symptom and not symptom_items:
            continue

        score = section_query_score(question, heading, body_text)
        lowered_heading = heading.lower()
        if require_action and action_items:
            score += 8
        if require_symptom and symptom_items:
            score += 6
        if "where to get help" in lowered_heading or "when to contact" in lowered_heading:
            score -= 10
        if "what this is" in lowered_heading or "things to know" in lowered_heading:
            score -= 6
        if score > best_score:
            best_heading = heading
            best_score = score

    return best_heading


def build_support_topic_title(question=None, source_name=None, section_heading=None, content_text=None):
    """
    Return the best available support title for the matched result.
    """
    guide_content = parse_guide_content(content_text)
    guide_title = (guide_content.get("TITLE") or "").strip() or format_source_name(source_name)
    wifi_intent = classify_wifi_query_intent(question) if is_wifi_support_content(content_text) else None

    if wifi_intent == "setup":
        return "Student Wi-Fi Setup"
    if wifi_intent == "connected_no_internet":
        return "Connected to Wi-Fi, but Websites Do Not Load"
    if wifi_intent == "not_visible":
        return "CCA-Students Is Not Showing"
    if wifi_intent == "password":
        return "Wi-Fi Password Help"
    if wifi_intent == "troubleshooting":
        return "Wi-Fi or Internet Not Working"

    preferred_heading = section_heading
    if is_direct_setup_query(question):
        action_heading = select_best_matching_section(
            question=question,
            content_text=content_text,
            require_action=True,
        )
        if action_heading:
            preferred_heading = action_heading
    elif not preferred_heading or heading_is_generic(preferred_heading):
        action_heading = select_best_matching_section(
            question=question,
            content_text=content_text,
            require_action=True,
        )
        if action_heading:
            preferred_heading = action_heading

    cleaned_heading = clean_section_heading(preferred_heading)
    if cleaned_heading:
        if source_name in {"d2l.txt", "d2l-troubleshooting.txt"}:
            d2l_title_override = {
                "how to access": "Accessing D2L / Brightspace",
                "try this first": "D2L or Course Access Help",
                "if that did not work": "D2L or Course Access Help",
                "course not showing": "Finding Your Online Class in D2L",
            }.get(normalize_text(cleaned_heading))
            if d2l_title_override:
                return d2l_title_override
        title_override = SUPPORT_TITLE_OVERRIDES.get(normalize_text(cleaned_heading))
        if title_override:
            return title_override
        if guide_title and heading_is_generic(preferred_heading):
            return guide_title
        if guide_title and normalize_text(cleaned_heading) == normalize_text(guide_title):
            return guide_title
        return cleaned_heading

    return guide_title or "Technology Support Help"


def classify_response_profile(question=None, source_name=None, section_heading=None, content_text=None):
    """
    Return a lightweight rendering profile for the matched support response.
    """
    lowered_question = normalize_text(question or "")
    lowered_heading = normalize_text(section_heading or "")
    wifi_intent = classify_wifi_query_intent(question) if is_wifi_support_content(content_text) else None

    explicit_contact_query = (
        source_name == "contact-it.txt"
        or "contact it" in lowered_question
        or "contact helpdesk" in lowered_question
        or "contact the helpdesk" in lowered_question
        or "helpdesk" in lowered_question
        or "help desk" in lowered_question
        or "it phone" in lowered_question
        or "phone number" in lowered_question
        or "talk to someone" in lowered_question
        or "submit a ticket" in lowered_question
    )

    if explicit_contact_query:
        return {
            "kind": "contact",
            "primary_label": "Contact details",
            "followup_label": "When to contact IT",
            "show_followup": False,
            "show_feedback": False,
            "escalation_title": "When to contact IT",
            "ticket_help_label": "Include when you contact IT",
        }

    if source_name == "mfa-account-security.txt":
        mfa_intent = classify_mfa_query_intent(question)
        return {
            "kind": "troubleshooting",
            "primary_label": "MFA recovery steps" if mfa_intent == "lost_access" else "Try this first",
            "followup_label": "Still not working?",
            "show_followup": True,
            "show_feedback": True,
            "escalation_title": "Need help from IT?",
            "ticket_help_label": "Include when you contact IT",
        }

    if source_name == "student-laptops-calculators.txt":
        if any(term in lowered_question for term in ("laptop", "calculator", "checkout", "borrow", "loan")):
            return {
                "kind": "checkout",
                "primary_label": "Checkout steps",
                "followup_label": "Still need help?",
                "show_followup": False,
                "show_feedback": False,
                "escalation_title": "Need more help?",
                "ticket_help_label": "Bring or include",
            }
        return {
            "kind": "informational",
            "primary_label": "What to do",
            "followup_label": "Still need help?",
            "show_followup": False,
            "show_feedback": True,
            "escalation_title": "Need more help?",
        }

    if is_direct_setup_query(question) or wifi_intent == "setup":
        return {
            "kind": "setup",
            "primary_label": "Try this first",
            "followup_label": "Still need help?",
            "show_followup": True,
            "show_feedback": True,
            "escalation_title": "Need help from IT?",
            "ticket_help_label": "Include when you contact IT",
        }

    if any(marker in lowered_question for marker in [normalize_text(marker) for marker in SYMPTOM_MARKERS]) or any(
        marker in lowered_heading for marker in ("not working", "not loading", "cannot", "issue", "problem")
    ):
        return {
            "kind": "troubleshooting",
            "primary_label": "Try this first",
            "followup_label": "Still not working?",
            "show_followup": True,
            "show_feedback": True,
            "escalation_title": "Need help from IT?",
            "ticket_help_label": "Include when you contact IT",
        }

    return {
        "kind": "informational",
        "primary_label": "What to do",
        "followup_label": "Still need help?",
        "show_followup": False,
        "show_feedback": True,
        "escalation_title": "Need more help?",
        "ticket_help_label": "Include when you ask for help",
    }


def build_contact_support_items(content_text):
    """
    Preserve contact-detail bullets that are not action-shaped troubleshooting steps.
    """
    if not content_text:
        return []

    guide_content = parse_guide_content(content_text)
    if guide_content.get("STEPS"):
        items = []
        for resolved in resolve_guide_items(guide_content["STEPS"], content_text):
            items.extend(heuristic_extract_step_items(resolved))
        return dedupe_preserve_order(items)

    section_map = parse_section_map(content_text)
    items = []
    for heading, body_text in section_map.items():
        if "contact" in heading.lower() or "ticket" in heading.lower():
            items.extend(heuristic_extract_step_items(body_text))
    return dedupe_preserve_order(items)


def _flatten_text_lines(text):
    if not text:
        return ""
    flattened_parts = []
    for part in text.splitlines():
        cleaned = part.strip()
        if not cleaned:
            continue
        if is_guide_metadata_line(cleaned) or is_internal_guide_text(cleaned):
            continue
        if cleaned.endswith(":") and not cleaned.startswith(("-", "•")):
            continue
        if cleaned.startswith(("-", "•")):
            cleaned = cleaned[1:].strip()
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
        if is_internal_guide_text(cleaned):
            continue
        flattened_parts.append(cleaned)
    return " ".join(flattened_parts).strip()


def _summary_sentences(text, limit=2):
    if not text:
        return []
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", _flatten_text_lines(text))
        if sentence.strip()
    ]
    return sentences[:limit]


def build_task_focused_summary(question, support_title=None):
    lowered = normalize_text(question or "")
    if not lowered:
        return None

    if "wifi" in lowered or "wi fi" in lowered or "wireless" in lowered:
        if "connect" in lowered:
            return "Follow these steps to connect your device to the campus Wi-Fi network."
        return "Use these steps to restore your campus Wi-Fi connection."

    if "d2l" in lowered or "brightspace" in lowered:
        if any(term in lowered for term in ("log", "sign", "access")):
            return "Follow these steps to sign in to D2L and confirm your access is working."
        return "Use these steps to restore access to D2L."
    if any(term in lowered for term in ("online class", "teacher", "homework", "course")):
        return "Use these steps to find D2L, open your course, and get to the class item you need."

    if "password" in lowered:
        return "Follow these steps to reset your password and confirm you can sign in again."

    if any(term in lowered for term in ("email", "outlook")):
        return "Follow these steps to access your email and confirm your account is working."

    if any(term in lowered for term in ("mfa", "multi factor", "multifactor", "verification code", "authenticator")):
        return "Use these steps to restore your MFA verification method and complete sign-in."
    return None


def build_quick_summary(
    question,
    source_name=None,
    section_heading=None,
    content_text=None,
    answer_text=None,
):
    """
    Build a short, calm summary for the matched support result.
    """
    guide_content = parse_guide_content(content_text)
    support_title = build_support_topic_title(
        question=question,
        source_name=source_name,
        section_heading=section_heading,
        content_text=content_text,
    )
    wifi_intent = classify_wifi_query_intent(question) if is_wifi_support_content(content_text) else None
    if wifi_intent == "setup":
        return (
            "Students should connect personal devices to CCA-Students. "
            "It is an open Wi-Fi network, and the consent page must be accepted before websites will load."
        )
    if wifi_intent == "connected_no_internet":
        return (
            "Your device may be connected to CCA-Students, but the consent page may still need to open "
            "before websites will load."
        )
    if wifi_intent == "not_visible":
        return "Use these checks when CCA-Students does not appear in your device's Wi-Fi list."
    if wifi_intent == "password":
        return "CCA-Students does not require a Wi-Fi password. Check that your device selected the student network."

    task_summary = build_task_focused_summary(question, support_title=support_title)
    if task_summary:
        return task_summary

    if guide_content.get("CONTEXT"):
        context_text = " ".join(resolve_guide_items(guide_content["CONTEXT"], content_text))
        context_sentences = _summary_sentences(context_text, limit=2)
        if context_sentences:
            first = context_sentences[0]
            summary_parts = [first]
            if support_title and section_heading and not heading_is_generic(section_heading):
                summary_parts.append("Start with these approved steps.")
            summary = " ".join(summary_parts + context_sentences[1:])
            summary = summary.strip()
            if summary:
                return summary

    answer_sentences = _summary_sentences(strip_guide_metadata_lines(answer_text), limit=2)
    if answer_sentences:
        summary = answer_sentences[0]
        if section_heading and heading_is_generic(section_heading) and support_title:
            return f"{summary} Use the steps below for this issue."
        return summary

    if question and question.strip():
        return "Use the steps below for this issue. Start with these approved steps."
    return "Start with the documented checks below."


def build_ticket_help_items(question=None, source_name=None, content_text=None, response_profile=None):
    """
    Return concise escalation prep bullets for contacting IT.
    """
    profile_kind = (response_profile or {}).get("kind")
    if profile_kind == "contact":
        return [
            "Include what you need help with.",
            "Include the device, app, or system involved.",
            "Include any exact error message or screenshot, if available.",
        ]

    if profile_kind == "checkout":
        return [
            "Bring your student ID.",
            "Bring or know your current course schedule.",
            "Explain what device or checkout item you need.",
            "Contact the listed office or support contact if you are unsure where to go.",
        ]

    items = [
        "Include the exact error message or screenshot.",
        "Include the device and browser/app you are using.",
        "Include what you already tried.",
    ]

    lowered_question = (question or "").lower()
    lowered_content = (content_text or "").lower()
    content_already_mentions_account_id = (
        "student id" in lowered_content
        and ("cca username" in lowered_content or "s#" in lowered_content)
    )
    if (
        source_name in {
            "password-reset.txt",
            "student-email.txt",
            "student-email-troubleshooting.txt",
            "mfa-account-security.txt",
            "d2l.txt",
            "d2l-troubleshooting.txt",
        }
        or any(term in lowered_question for term in ("login", "password", "account", "mfa", "email", "d2l"))
    ):
        if not content_already_mentions_account_id:
            items.append("Include your student ID or CCA username only if this is an account issue.")

    return dedupe_preserve_order(items)


def build_escalation_summary_text(escalation_text, response_profile=None):
    """
    Keep the IT help box concise when KB escalation sections repeat contact lines.
    """
    if not escalation_text:
        return None

    profile_kind = (response_profile or {}).get("kind")
    if profile_kind == "contact":
        return "Use the contact options above for CCA technology support."

    lines = []
    has_contact_instruction = False
    for line in escalation_text.splitlines():
        cleaned = re.sub(r"^[-•\s]+", "", line).strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if (
            "contact" in lowered
            and (
                "cca it" in lowered
                or "it support" in lowered
                or "helpdesk" in lowered
                or "help desk" in lowered
            )
        ):
            has_contact_instruction = True
            continue
        lines.append(cleaned)

    deduped = dedupe_preserve_order(lines)
    if has_contact_instruction:
        deduped.insert(
            0,
            "Contact the CCA IT Helpdesk if the issue continues after trying these steps.",
        )

    return "\n".join(dedupe_preserve_order(deduped[:3])) or None


def build_no_steps_message():
    return (
        "This guide identifies the issue, but does not include enough step-by-step instructions. "
        "Contact IT with the details below."
    )


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


def detect_disambiguation_options(question, query_analysis=None):
    """
    Return workflow options for broad, ambiguous support questions.
    """
    if not question:
        return []

    normalized = " ".join(question.lower().split())
    normalized_for_mfa = normalize_text(question)
    mfa_clarification_phrases = {
        "mfa is not working",
        "my mfa is not working",
        "mfa not working",
        "verification code is not working",
        "the verification code is not working",
        "duo keeps asking me again",
        "duo keeps asking me",
        "duo keeps prompting me",
        "duo verification is not working",
        "duo not working",
    }
    if normalized_for_mfa in mfa_clarification_phrases or normalized_for_mfa.startswith("duo "):
        return [
            {
                "label": "Student Microsoft Authenticator",
                "query": "Microsoft Authenticator is not working",
            },
            {"label": "Faculty/Staff Duo", "query": "Contact IT"},
            {"label": "I'm not sure", "query": "Contact IT"},
        ]

    broad_access_phrases = {
        "it won t let me in",
        "it wont let me in",
        "it won t let me log in",
        "it won t let me login",
        "it wont let me log in",
        "it wont let me login",
        "can t get in",
        "cant get in",
    }
    broad_access_options = [
        {"label": "D2L", "query": "I cannot log into D2L"},
        {"label": "Student email", "query": "I cannot log into student email"},
        {"label": "MyCCA", "query": "My MyCCA account login is not working"},
        {"label": "Campus computer", "query": "I cannot log into a CCA computer"},
        {"label": "Wi-Fi", "query": "I cannot sign into Wi-Fi"},
        {"label": "MFA/Auth", "query": "MFA is not working"},
        {"label": "I'm not sure", "query": "Contact IT"},
    ]
    if normalized_for_mfa in broad_access_phrases:
        return broad_access_options

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
        "mfa",
        "verification",
        "authenticator",
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

    classifier_intent = (query_analysis or {}).get("intent", "")
    classifier_topic = (query_analysis or {}).get("topic", "")

    if classifier_topic in {"wifi", "email", "d2l", "zoom", "classroom"} and classifier_intent in {
        "troubleshooting",
        "access",
        "contact",
    }:
        return []

    if any(phrase in normalized for phrase in login_phrases):
        return broad_access_options

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
        if classifier_topic == "wifi":
            return [
                {"label": "Wi-Fi", "query": "I cannot connect to CCA Wi-Fi"},
                {
                    "label": "I'm not sure",
                    "query": "I need help finding the right IT support option",
                },
            ]
        return [
            {"label": "D2L", "query": "I cannot access D2L"},
            {"label": "Email", "query": "I cannot access my student email"},
            {"label": "Zoom", "query": "I cannot access Zoom for class"},
            {"label": "Course videos", "query": "I cannot access YuJa videos in my course"},
        ]

    if any(phrase in normalized for phrase in not_working_phrases):
        if classifier_topic == "classroom":
            return [
                {"label": "Display", "query": "Classroom display won’t turn on"},
                {"label": "Projector", "query": "Projector has no signal"},
                {"label": "Audio", "query": "Audio not working in classroom"},
                {
                    "label": "I'm not sure",
                    "query": "I need help finding the right IT support option",
                },
            ]
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
        context_text = " ".join(resolve_guide_items(guide_content["CONTEXT"], content_text))
        if is_internal_guide_text(context_text):
            return None
        lowered = context_text.lower().strip()
        lowered = re.sub(r"^[-•\s]+", "", lowered)
        generic_starts = (
            "use this guide",
            "this guide helps",
            "this guide is used when",
            "it covers",
            "information about",
            "this guide is for",
        )
        if lowered.startswith(generic_starts):
            return None
        return context_text
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

    return dedupe_preserve_order(items)


def steps_are_escalation_only(step_items):
    """
    Detect when extracted steps are really just escalation/contact instructions.
    """
    if not step_items:
        return False

    normalized = [item.strip().lower() for item in step_items if item.strip()]
    if not normalized:
        return False

    contact_like = 0
    for item in normalized:
        if (
            "contact" in item
            or "it support" in item
            or "helpdesk" in item
            or "help desk" in item
            or "who to contact" in item
            or "call" in item
            or "phone:" in item
        ):
            contact_like += 1
    return contact_like == len(normalized)


def extract_common_symptoms(answer_text, content_text=None, question=None, section_heading=None):
    """
    Return symptom/problem statements without mixing them into action steps.
    """
    if is_direct_setup_query(question):
        return []

    symptoms = []

    if section_heading and heading_is_generic(section_heading):
        section_map = parse_section_map(content_text)
        matched_text = section_map.get(section_heading, "")
        symptoms.extend(filter_symptom_items(heuristic_extract_step_items(matched_text)))
    elif section_heading and is_probable_symptom_line(section_heading):
        symptoms.append(clean_section_heading(section_heading))

    symptoms.extend(filter_symptom_items(heuristic_extract_step_items(answer_text)))

    if not symptoms and content_text:
        symptom_heading = select_best_matching_section(
            question=question,
            content_text=content_text,
            require_symptom=True,
        )
        if symptom_heading:
            section_map = parse_section_map(content_text)
            symptoms.extend(
                filter_symptom_items(heuristic_extract_step_items(section_map.get(symptom_heading, "")))
            )

    return dedupe_preserve_order(symptoms)


def extract_step_items(answer_text, content_text=None, question=None, section_heading=None):
    """
    Prefer structured STEPS data when available, else fall back to heuristic extraction.
    """
    lowered_question = (question or "").lower()
    lowered_heading = (section_heading or "").lower()
    contact_intent = (
        lowered_question.startswith("where ")
        or lowered_question.startswith("who ")
        or lowered_question.startswith("when ")
        or "who do i" in lowered_question
        or "where do i" in lowered_question
        or "when should i" in lowered_question
        or "contact" in lowered_question
    )
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
    direct_section_headings = {
        "zoom sso login:",
        "zoom company domain:",
        "zoom license not showing:",
        "mapping a shared printer in windows:",
        "printer error message:",
        "adding an alternate mfa method:",
    }
    if lowered_heading in direct_section_headings:
        direct_section_query = True

    if direct_section_query:
        direct_steps = filter_action_items(heuristic_extract_step_items(answer_text))
        if direct_steps:
            return direct_steps

    wifi_intent = classify_wifi_query_intent(question) if is_wifi_support_content(content_text) else None
    wifi_intent_headings = {
        "setup": "First-time setup:",
        "connected_no_internet": "If you are connected but websites do not load:",
        "not_visible": "If you do not see CCA-Students:",
        "password": "If your password does not work:",
        "troubleshooting": "Internet or network not working:",
    }
    if wifi_intent in wifi_intent_headings:
        intent_steps = resolve_section_steps_by_heading(
            content_text,
            wifi_intent_headings[wifi_intent],
        )
        if intent_steps:
            return intent_steps

    mfa_intent = classify_mfa_query_intent(question) if is_mfa_support_content(content_text) else None
    if mfa_intent == "alternate_method":
        alternate_steps = resolve_section_steps_by_heading(content_text, "Adding an alternate MFA method:")
        if alternate_steps:
            return alternate_steps

    if mfa_intent == "lost_access":
        first_steps = resolve_section_steps_by_heading(content_text, "Try this first:")
        section_map_for_mfa = parse_section_map(content_text)
        lost_steps = heuristic_extract_step_items(
            section_map_for_mfa.get("Changed phones or lost MFA access:", "")
        )
        selected_steps = []
        for index in (1, 2, 3, 4):
            if index < len(first_steps):
                selected_steps.append(first_steps[index])
        for step in lost_steps:
            if "old verification method may still be attached" in step.lower() and any(
                "old verification method may still be attached" in existing.lower()
                for existing in selected_steps
            ):
                continue
            selected_steps.append(step)
        concise_steps = dedupe_preserve_order(selected_steps)
        if concise_steps:
            return concise_steps[:6]

    if mfa_intent == "troubleshooting":
        mfa_steps = resolve_section_steps_by_heading(content_text, "Common MFA problems:")
        if mfa_steps:
            return mfa_steps[:5]

    section_map = parse_section_map(content_text)
    best_action_heading = select_best_matching_section(
        question=question,
        content_text=content_text,
        require_action=True,
    )
    if is_direct_setup_query(question) and best_action_heading and best_action_heading in section_map:
        best_section_steps = filter_action_items(
            heuristic_extract_step_items(section_map[best_action_heading])
        )
        if best_section_steps:
            return best_section_steps

    if section_heading and section_heading in section_map:
        matched_section_steps = filter_action_items(
            heuristic_extract_step_items(section_map[section_heading])
        )
        if len(matched_section_steps) >= 2 and (
            contact_intent or not steps_are_escalation_only(matched_section_steps)
        ):
            return matched_section_steps

    if best_action_heading and best_action_heading in section_map:
        best_section_steps = filter_action_items(
            heuristic_extract_step_items(section_map[best_action_heading])
        )
        if best_section_steps:
            return best_section_steps

    guide_content = parse_guide_content(content_text)
    if guide_content.get("STEPS"):
        if section_heading and section_heading in set(guide_content.get("STEPS", [])):
            matched_steps = resolve_guide_items([section_heading], content_text)
            steps = []
            for resolved in matched_steps:
                steps.extend(filter_action_items(heuristic_extract_step_items(resolved)))
            if len(steps) >= 2 and (contact_intent or not steps_are_escalation_only(steps)):
                return steps

        steps = []
        for resolved in resolve_guide_items(guide_content["STEPS"], content_text):
            extracted = filter_action_items(heuristic_extract_step_items(resolved))
            if extracted:
                steps.extend(extracted)
        cleaned = dedupe_preserve_order(steps)
        if cleaned:
            return cleaned

    fallback_steps = filter_action_items(heuristic_extract_step_items(answer_text))
    if fallback_steps and (contact_intent or not steps_are_escalation_only(fallback_steps)):
        return fallback_steps

    if guide_content.get("STEPS"):
        steps = []
        for resolved in resolve_guide_items(guide_content["STEPS"], content_text):
            extracted = filter_action_items(heuristic_extract_step_items(resolved))
            steps.extend(extracted)
        deduped = dedupe_preserve_order(steps)
        if deduped:
            return deduped

    return []


def dedupe_wifi_followup_steps(steps, limit=5):
    """
    Keep Wi-Fi follow-up branches concise by avoiding repeated action families.
    """
    deduped = dedupe_preserve_order(steps)
    result = []
    seen_categories = set()
    for step in deduped:
        lowered = step.lower()
        if "contact" in lowered or "helpdesk" in lowered:
            category = "contact"
        elif "restart" in lowered or "turn wi-fi off" in lowered or "turn wi-fi back on" in lowered:
            category = "restart"
        elif "reconnect" in lowered or "connect again" in lowered:
            category = "reconnect"
        elif "password" in lowered or "sign in" in lowered:
            category = "password"
        elif "browser" in lowered or "website" in lowered or "consent" in lowered or "splash" in lowered:
            category = "browser"
        elif "cca-students" in lowered and any(term in lowered for term in ("see", "appear", "show", "list")):
            category = "network-visible"
        else:
            category = normalize_text(step)[:80]

        if category in seen_categories:
            continue
        seen_categories.add(category)
        result.append(step)
        if len(result) >= limit:
            break

    return result


def build_additional_troubleshooting_steps(question, source_name=None, content_text=None):
    """
    Provide simple next-step guidance when the first procedure did not resolve the issue.
    """
    wifi_intent = classify_wifi_query_intent(question) if is_wifi_support_content(content_text) else None
    if wifi_intent:
        def first_action(heading):
            steps = resolve_section_steps_by_heading(content_text, heading)
            return steps[0] if steps else None

        branch_headings = []
        if wifi_intent == "setup":
            branch_headings = [
                ("If you do not see CCA-Students", "If you do not see CCA-Students:"),
                ("If you are connected but websites do not load", "If you are connected but websites do not load:"),
                ("If your password does not work", "If your password does not work:"),
            ]
        elif wifi_intent == "connected_no_internet":
            branch_headings = [
                ("If the network keeps dropping", "Wi-Fi keeps dropping or is unstable:"),
                ("If CCA-Students disappears", "If you do not see CCA-Students:"),
                ("If your device asks for a Wi-Fi password", "If your password does not work:"),
            ]
        elif wifi_intent == "not_visible":
            branch_headings = [
                ("If you later connect but websites do not load", "If you are connected but websites do not load:"),
                ("If your device asks for a Wi-Fi password", "If your password does not work:"),
            ]
        elif wifi_intent == "password":
            branch_headings = [
                ("If your CCA account password is the problem", "If your password does not work:", 2),
                ("If CCA-Students does not appear", "If you do not see CCA-Students:", 0),
            ]
        elif wifi_intent == "troubleshooting":
            branch_headings = [
                ("If websites do not load", "If you are connected but websites do not load:"),
                ("If CCA-Students does not appear", "If you do not see CCA-Students:"),
                ("If the connection keeps dropping", "Wi-Fi keeps dropping or is unstable:"),
            ]

        branch_steps = []
        seen_headings = {}
        for branch in branch_headings:
            label = branch[0]
            heading = branch[1]
            preferred_index = branch[2] if len(branch) > 2 else None
            steps = resolve_section_steps_by_heading(content_text, heading)
            index = preferred_index if preferred_index is not None else seen_headings.get(heading, 0)
            if index >= len(steps):
                continue
            if preferred_index is None:
                seen_headings[heading] = index + 1
            step = steps[index]
            branch_steps.append(f"{label}: {step}")

        return dedupe_wifi_followup_steps(branch_steps, limit=5)

    guide_content = parse_guide_content(content_text)
    if guide_content.get("IF NOT FIXED"):
        steps = []
        for resolved in resolve_guide_items(guide_content["IF NOT FIXED"], content_text):
            extracted = filter_action_items(heuristic_extract_step_items(resolved))
            if extracted:
                steps.extend(extracted)
        steps = dedupe_preserve_order(steps)
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
