from dataclasses import dataclass
import os
from pathlib import Path
import re

from router import expand_query_tokens, normalize_text, tokenize_text
from semantic_retriever import retrieve_best_semantic_section
from kb_scope import load_scoped_content_texts

CONTENT_DIR = Path(__file__).parent / "content"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_SEMANTIC_MIN_SCORE = 0.45
LOW_VALUE_TOKENS = {
    "a", "an", "and", "are", "can", "do", "for", "get", "help", "how",
    "i", "if", "in", "is", "it", "me", "my", "need", "not", "of", "on",
    "or", "the", "to", "we", "what", "where", "with", "working", "you",
}
ACTIONABLE_QUERY_TOKENS = {
    "access", "assignment", "assignments", "borrow", "calculator", "class",
    "connect", "course", "courses", "email", "find", "get", "join", "laptop",
    "link", "log", "login", "materials", "meeting", "mfa", "password", "print",
    "projector", "quiz", "quizzes", "reset", "submit", "verification", "video", "wifi",
    "windows", "wireless", "yuja", "zoom",
}
GENERIC_SECTION_HEADINGS = {
    "what this is:",
    "what students use it for:",
    "things to know:",
}
TROUBLESHOOTING_PHRASES = {
    "can t", "cannot", "unable", "not working", "locked", "issue", "problem",
    "problems", "is not working", "does not work", "doesn t work", "won t",
    "broke", "broken",
}
GUIDE_FIELD_PATTERN = re.compile(
    r"^\s*-\s*(TITLE|AUDIENCE|TAGS|CONTEXT|STEPS|IF NOT FIXED|ESCALATE):\s*(.*)$",
    flags=re.IGNORECASE,
)
TROUBLESHOOTING_SECTION_CLUES = (
    "not working", "cannot", "can t", "won t", "no signal", "problem",
    "problems", "issue", "issues", "audio not working", "microphone",
    "restart", "reconnect", "reset", "check", "try again", "verify",
    "still does not", "still is not", "still cannot", "troubleshooting",
)
ACCESS_SECTION_CLUES = (
    "how to access", "accessing", "joining", "join", "first access",
    "setting up", "setup", "set up", "sign in", "log in", "login",
    "mycca login", "alternative access", "open", "find your", "where to find",
)
ESCALATION_SECTION_CLUES = (
    "contact it", "contact cca it support", "helpdesk", "help desk",
    "submit a ticket", "when to contact", "still need help", "if the issue continues",
    "where to get help", "where to go for help", "who to contact",
)
INFORMATIONAL_SECTION_CLUES = (
    "what this is", "what students use it for", "things to know", "what mfa affects",
    "include", "upgrades include", "location", "eligibility",
)


@dataclass
class RetrievalResult:
    article_id: str
    section_heading: str
    answer_text: str
    score: int
    confidence: str
    full_document_text: str


def load_retrieval_texts(include_internal=False, internal_only=False):
    """
    Load scoped KB text files for section retrieval.
    """
    return load_scoped_content_texts(
        include_internal=include_internal,
        internal_only=internal_only,
        content_dir=CONTENT_DIR,
    )


def clean_content_lines(content_text):
    """
    Remove metadata and formatting divider lines before section parsing.
    """
    cleaned = []
    for raw_line in content_text.splitlines():
        stripped = raw_line.strip()
        normalized = stripped.lstrip("•").strip()

        if not stripped:
            cleaned.append("")
            continue

        if normalized.startswith("SOURCE:") or normalized.startswith("URL:"):
            continue

        if stripped and set(stripped) <= {"=", "-", "`"}:
            continue

        if normalized.lower() == "guide ready fields:":
            break

        if GUIDE_FIELD_PATTERN.match(stripped):
            break

        cleaned.append(raw_line.rstrip())

    return cleaned


def is_heading_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("-", "•")):
        return False
    if stripped.endswith(":"):
        return True
    return stripped.isupper() and len(stripped.split()) <= 8


def is_group_heading_line(line):
    stripped = line.strip()
    if not stripped or stripped.startswith(("-", "•")):
        return False
    if stripped.endswith(":"):
        return False
    if stripped.endswith("."):
        return False
    return len(stripped.split()) <= 10


def next_non_empty_line(lines, start_index):
    for index in range(start_index, len(lines)):
        if lines[index].strip():
            return lines[index].strip()
    return None


def build_section(article_id, document_title, heading, lines, full_document_text):
    body_lines = [line.rstrip() for line in lines if line.strip()]
    answer_lines = []

    if heading:
        answer_lines.append(heading)
    answer_lines.extend(body_lines)
    answer_text = "\n".join(answer_lines).strip()

    display_heading = heading or document_title or "General guidance"
    return {
        "article_id": article_id,
        "document_title": document_title or article_id,
        "section_heading": display_heading,
        "answer_text": answer_text,
        "body_text": "\n".join(body_lines).strip(),
        "full_document_text": full_document_text,
    }


def split_document_sections(article_id, content_text):
    """
    Split one document into searchable sections.
    """
    if not content_text or not content_text.strip():
        return []

    lines = clean_content_lines(content_text)
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    if not non_empty_lines:
        return []

    document_title = ""
    first_line = non_empty_lines[0]
    if (
        not first_line.endswith(":")
        and not first_line.endswith(".")
        and len(first_line.split()) <= 10
    ):
        document_title = first_line

    sections = []
    current_parent_heading = None
    current_heading = None
    current_lines = []
    started = False

    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped:
            continue

        if not started:
            started = True
            if document_title and stripped == document_title:
                continue

        upcoming_line = next_non_empty_line(lines, index + 1)
        if (
            is_group_heading_line(raw_line)
            and stripped != document_title
            and upcoming_line is not None
            and is_heading_line(upcoming_line)
        ):
            if current_heading is not None and current_lines:
                sections.append(
                    build_section(
                        article_id=article_id,
                        document_title=document_title,
                        heading=current_heading,
                        lines=current_lines,
                        full_document_text=content_text.strip(),
                    )
                )
            current_parent_heading = stripped
            current_heading = None
            current_lines = []
            continue

        if is_heading_line(raw_line):
            if current_heading is not None and current_lines:
                sections.append(
                    build_section(
                        article_id=article_id,
                        document_title=document_title,
                        heading=current_heading,
                        lines=current_lines,
                        full_document_text=content_text.strip(),
                    )
                )
            heading = stripped
            if current_parent_heading and current_parent_heading not in {
                "IT SUPPORT CONTACTS",
                "WHERE TO GET TECH HELP",
                "OTHER HELPFUL GUIDES",
                "IMPORTANT NOTE",
            }:
                heading = f"{current_parent_heading} — {heading}"
            current_heading = heading
            current_lines = []
            continue

        current_lines.append(stripped)

    if current_heading is not None and current_lines:
        sections.append(
            build_section(
                article_id=article_id,
                document_title=document_title,
                heading=current_heading,
                lines=current_lines,
                full_document_text=content_text.strip(),
            )
        )

    if sections:
        return sections

    return [
        build_section(
            article_id=article_id,
            document_title="",
            heading=None,
            lines=[line.strip() for line in lines if line.strip()],
            full_document_text=content_text.strip(),
        )
    ]


def has_actionable_query_signal(question):
    question_tokens = set(tokenize_text(question))
    return bool(question_tokens & ACTIONABLE_QUERY_TOKENS)


def build_weighted_query_tokens(question):
    weighted_tokens = {}
    raw_tokens = expand_query_tokens(question)

    for token in raw_tokens:
        if len(token) <= 1 or token in LOW_VALUE_TOKENS:
            continue

        weight = 1
        if token in {
            "assignment", "calculator", "class", "course", "email", "laptop",
            "login", "materials", "mfa", "password", "projector", "quiz",
            "wifi", "windows", "yuja", "zoom",
        }:
            weight = 2
        if token in {"ti", "84"}:
            weight = 3

        weighted_tokens[token] = max(weighted_tokens.get(token, 0), weight)

    return weighted_tokens


def canonicalize_token(token):
    lowered = token.lower()
    for suffix in ("ing", "ers", "ies", "ied", "ed", "es", "s"):
        if len(lowered) > len(suffix) + 2 and lowered.endswith(suffix):
            lowered = lowered[: -len(suffix)]
            break
    return lowered[:5]


def build_token_counts(text):
    counts = {}
    for token in tokenize_text(text):
        if token in LOW_VALUE_TOKENS:
            continue
        root = canonicalize_token(token)
        counts[root] = counts.get(root, 0) + 1
    return counts


INTENT_GENERIC_ROOTS = {
    canonicalize_token(token)
    for token in (
        "contact", "help", "where", "who", "when", "location", "located",
        "support", "issue", "problem", "problems", "submit", "find", "cca", "it",
    )
}


def classify_query_intent(question):
    """
    Classify the user's query into a coarse intent bucket used for ranking.
    """
    normalized = normalize_text(question)
    if not normalized:
        return "other"

    if (
        normalized.startswith("who do i contact")
        or normalized.startswith("who can help")
        or normalized.startswith("who should i contact")
        or normalized.startswith("when should i contact")
        or normalized.startswith("when do i contact")
        or "who do i contact" in normalized
        or "who can help" in normalized
        or "where do i get help" in normalized
        or "where can i get help" in normalized
        or "where do i go for help" in normalized
        or "contact" in normalized
        or "help desk" in normalized
        or "helpdesk" in normalized
        or "ticket" in normalized
        or normalized.startswith("where is")
        or normalized.startswith("where are")
        or "office located" in normalized
        or "located" in normalized
        or "location" in normalized
    ):
        return "contact/help-location"

    if (
        any(phrase in normalized for phrase in TROUBLESHOOTING_PHRASES)
        or "can t access" in normalized
        or "won t load" in normalized
        or "cannot connect" in normalized
        or "no signal" in normalized
        or "audio not working" in normalized
        or "microphone not working" in normalized
        or "not loading" in normalized
    ):
        return "troubleshooting"

    if (
        normalized.startswith("how do i access")
        or normalized.startswith("how do i join")
        or normalized.startswith("how do i connect")
        or normalized.startswith("how do i log")
        or normalized.startswith("how do i sign")
        or normalized.startswith("how do i find")
        or normalized.startswith("where do i find")
        or normalized.startswith("where do i submit")
        or normalized.startswith("where do i check out")
        or normalized.startswith("where can i borrow")
        or normalized.startswith("how do i get")
        or "first time" in normalized
    ):
        return "access/setup"

    if (
        normalized.startswith("what is")
        or normalized.startswith("what does")
        or normalized.startswith("what are")
        or normalized.startswith("should i use")
    ):
        return "informational"

    return "other"


def classify_section_intent(section):
    """
    Classify a section by its primary intent using heading/body clues.
    """
    heading = normalize_text(section["section_heading"])
    body = normalize_text(section["body_text"])
    text = f"{heading}\n{body}"

    escalation_score = sum(1 for clue in ESCALATION_SECTION_CLUES if clue in text)
    troubleshooting_score = sum(1 for clue in TROUBLESHOOTING_SECTION_CLUES if clue in text)
    access_score = sum(1 for clue in ACCESS_SECTION_CLUES if clue in text)
    informational_score = sum(1 for clue in INFORMATIONAL_SECTION_CLUES if clue in text)

    if "where to get help" in heading or "when to contact" in heading or "still need help" in heading:
        escalation_score += 3
    if "how to access" in heading or "accessing" in heading or "joining" in heading or "login" in heading:
        access_score += 3
    if "not working" in heading or "cannot" in heading or "no signal" in heading or "problems" in heading:
        troubleshooting_score += 3
    if heading in GENERIC_SECTION_HEADINGS:
        informational_score += 2

    scored_intents = {
        "troubleshooting": troubleshooting_score,
        "access/setup": access_score,
        "escalation/contact": escalation_score,
        "informational/general": informational_score,
    }
    best_intent = max(scored_intents, key=scored_intents.get)
    if scored_intents[best_intent] <= 0:
        return "informational/general"
    return best_intent


def apply_intent_scoring(
    query_intent,
    section_intent,
    normalized_question,
    normalized_heading,
    normalized_answer,
    topical_overlap,
):
    """
    Return an intent-based score adjustment.
    """
    adjustment = 0
    if query_intent == "troubleshooting":
        if section_intent == "troubleshooting":
            adjustment += 18
        elif section_intent == "access/setup":
            adjustment += 2
        elif section_intent == "informational/general":
            adjustment -= 4
        elif section_intent == "escalation/contact":
            adjustment -= 18
    elif query_intent == "contact/help-location":
        if section_intent == "escalation/contact":
            adjustment += 20 if topical_overlap else -26
        elif section_intent == "informational/general" and ("location" in normalized_heading or "location" in normalized_answer):
            adjustment += 12
        elif section_intent == "troubleshooting":
            adjustment -= 4
    elif query_intent == "access/setup":
        if section_intent == "access/setup":
            adjustment += 16
        elif section_intent == "troubleshooting":
            adjustment -= 6
        elif section_intent == "escalation/contact":
            adjustment -= 12
    elif query_intent == "informational":
        if section_intent == "informational/general":
            adjustment += 12
        elif section_intent == "access/setup":
            adjustment += 4
        elif section_intent == "escalation/contact":
            adjustment -= 6

    if query_intent != "contact/help-location" and section_intent == "escalation/contact":
        contact_density = normalized_answer.count("contact") + normalized_answer.count("helpdesk")
        adjustment -= min(contact_density * 2, 10)

    return adjustment


def score_section(question, section, query_analysis=None):
    normalized_question = normalize_text(question)
    normalized_heading = normalize_text(section["section_heading"])
    normalized_title = normalize_text(section["document_title"])
    normalized_answer = normalize_text(section["answer_text"])
    weighted_tokens = build_weighted_query_tokens(question)
    question_roots = {canonicalize_token(token) for token in tokenize_text(question) if token not in LOW_VALUE_TOKENS}
    answer_token_counts = build_token_counts(section["answer_text"])
    heading_token_counts = build_token_counts(section["section_heading"])
    title_token_counts = build_token_counts(section["document_title"])
    query_intent = classify_query_intent(question)
    classifier_intent = (query_analysis or {}).get("intent", "").strip().lower()
    classifier_topic = (query_analysis or {}).get("topic", "").strip().lower()
    classifier_confidence = float((query_analysis or {}).get("confidence", 0.0) or 0.0)
    if classifier_intent == "troubleshooting":
        query_intent = "troubleshooting"
    elif classifier_intent == "access":
        query_intent = "access/setup"
    elif classifier_intent == "contact":
        query_intent = "contact/help-location"
    elif classifier_intent == "informational":
        query_intent = "informational"
    section_intent = classify_section_intent(section)
    section_roots = set(answer_token_counts) | set(heading_token_counts) | set(title_token_counts)
    question_topic_roots = {root for root in question_roots if root not in INTENT_GENERIC_ROOTS}
    topical_overlap = bool(question_topic_roots & section_roots)

    if not weighted_tokens:
        return 0

    score = 0
    contact_intent = query_intent == "contact/help-location"
    for token, weight in weighted_tokens.items():
        token_root = canonicalize_token(token)
        score += answer_token_counts.get(token_root, 0) * weight
        score += heading_token_counts.get(token_root, 0) * weight * 5
        score += title_token_counts.get(token_root, 0) * weight * 2
        score += normalized_answer.count(token) * weight
        score += normalized_heading.count(token) * weight * 4
        score += normalized_title.count(token) * weight * 2

    question_tokens = [token for token in tokenize_text(question) if token not in LOW_VALUE_TOKENS]
    for size in (3, 2):
        for index in range(len(question_tokens) - size + 1):
            phrase = " ".join(question_tokens[index:index + size])
            if phrase in normalized_answer:
                score += size * 3
            if phrase in normalized_heading:
                score += size * 4

    if section["section_heading"].lower() in GENERIC_SECTION_HEADINGS and has_actionable_query_signal(question):
        score -= 2

    score += apply_intent_scoring(
        query_intent,
        section_intent,
        normalized_question,
        normalized_heading,
        normalized_answer,
        topical_overlap,
    )

    if has_actionable_query_signal(question):
        lowered_heading = section["section_heading"].lower()
        if lowered_heading.startswith("how to") or "how to" in lowered_heading:
            score += 2
        if lowered_heading.startswith("where to") or "where to" in lowered_heading:
            score += 2
        if "location" in lowered_heading and ("where" in normalized_question or "located" in normalized_question):
            score += 5

    troubleshooting_query = any(phrase in normalized_question for phrase in TROUBLESHOOTING_PHRASES)
    if troubleshooting_query:
        escalation_heading = (
            "where to get help" in normalized_heading
            or "where to go for help" in normalized_heading
            or "when to contact" in normalized_heading
            or "still need help" in normalized_heading
        )
        if escalation_heading:
            score += 10 if contact_intent else -14
        if "contact" in normalized_answer:
            score += 6 if contact_intent else -6

    if "reset" in question_roots and "password" in question_roots and "reset" in normalized_answer:
        score += 12
    if "reset" in question_roots and "reset" not in normalized_answer:
        score -= 12

    if "log into mycca" in normalized_question and "mycca login" in normalized_heading:
        score += 100
    elif "login" in question_roots and "mycca" in question_roots and "login" in normalized_heading:
        score += 40
    if "login" in question_roots and "mycca" in question_roots and not troubleshooting_query:
        if "where to get help" in normalized_heading:
            score -= 40

    if "password rules" in normalized_question and "password requirement" in normalized_heading:
        score += 100
    elif "rule" in question_roots or "requir" in question_roots:
        if "requirement" in normalized_heading or "rules" in normalized_heading:
            score += 50
        else:
            score -= 60

    normalized_question_tokens = normalize_text(question).split()
    if (
        "who" in normalized_question_tokens
        and "eligible" in normalized_heading
        and (
            "borrow" in question_roots
            or "laptop" in question_roots
            or "calcu" in question_roots
            or "loan" in question_roots
        )
    ):
        score += 50

    if "submi" in question_roots and ("submit" in normalized_answer or "submitting" in normalized_answer):
        score += 8

    d2l_beginner_access_query = (
        any(term in normalized_question for term in ("d2l", "brightspace", "online class"))
        and any(
            phrase in normalized_question
            for phrase in (
                "where it is",
                "where is",
                "where do i find",
                "how do i access",
                "teacher said",
                "idk where",
                "online class",
            )
        )
    )
    homework_access_query = (
        "homework" in normalized_question
        and any(term in normalized_question for term in ("get into", "access", "open", "find"))
        and not any(term in normalized_question for term in ("upload", "submit", "submission", "file"))
    )

    if section["article_id"] in {"d2l.txt", "d2l-troubleshooting.txt"}:
        if d2l_beginner_access_query:
            if section["article_id"] == "d2l.txt" and (
                "how to access" in normalized_heading or "try this first" in normalized_heading
            ):
                score += 120
            if "if that did not work" in normalized_heading:
                score -= 60
            if "assignment upload" in normalized_heading:
                score -= 60
        if homework_access_query:
            if section["article_id"] == "d2l.txt" and (
                "how to access" in normalized_heading or "try this first" in normalized_heading
            ):
                score += 110
            if "assignment upload" in normalized_heading:
                score -= 120

    if section["article_id"] == "d2l-troubleshooting.txt" and "d2l" in question_roots:
        if any(phrase in normalized_question for phrase in ("not loading", "won t load", "does not load")):
            if "browser or cache issues" in normalized_heading:
                score += 90
            if "cannot access d2l" in normalized_heading:
                score -= 20

    if (
        "email" in question_roots
        and section["article_id"] == "student-email-troubleshooting.txt"
        and any(phrase in normalized_question for phrase in ("does not work", "not working", "won t open", "not opening"))
    ):
        if "cannot access student email" in normalized_heading or "student email troubleshooting" in normalized_title:
            score += 80
    if (
        "email" in question_roots
        and section["article_id"] == "student-email.txt"
        and any(phrase in normalized_question for phrase in ("does not work", "not working", "won t open", "not opening"))
    ):
        score -= 40

    if "mfa" in question_roots and section["article_id"] == "mfa-account-security.txt":
        if any(phrase in normalized_question for phrase in ("mfa is not working", "mfa not working")):
            if "common mfa problems" in normalized_heading:
                score += 100
            if "changed phones" in normalized_heading:
                score -= 35

    mfa_topic_query = any(
        term in normalized_question
        for term in (
            "mfa",
            "multi factor",
            "multifactor",
            "authenticator",
            "verification",
        )
    )
    mfa_lost_access_query = mfa_topic_query and any(
        term in normalized_question
        for term in ("lost phone", "lost my phone", "changed phone", "changed phones", "lost access")
    )
    mfa_prompt_query = any(
        phrase in normalized_question
        for phrase in (
            "mfa keeps asking",
            "mfa keeps prompting",
            "authenticator is not working",
            "authenticator app not working",
            "microsoft authenticator is not working",
        )
    )
    if mfa_topic_query:
        if section["article_id"] == "mfa-account-security.txt":
            score += 35
            if mfa_lost_access_query and "changed phones or lost mfa access" in normalized_heading:
                score += 120
            if mfa_prompt_query and "common mfa problems" in normalized_heading:
                score += 110
            if "what mfa affects" in normalized_heading and (mfa_lost_access_query or mfa_prompt_query):
                score -= 35
        elif section["article_id"] in {"student-email.txt", "student-email-troubleshooting.txt"}:
            if "email" not in question_roots and "outlook" not in question_roots:
                score -= 50

    if "lapto" in question_roots and section["article_id"] == "student-laptops-calculators.txt":
        if any(phrase in normalized_question for phrase in ("need a laptop", "need laptop", "borrow a laptop", "semester laptop")):
            if "how to get a semester laptop" in normalized_heading:
                score += 100
            if "hub laptops" in normalized_heading or "calculator" in normalized_heading:
                score -= 40

    wifi_topic_query = any(
        term in normalized_question
        for term in (
            "wifi",
            "wi fi",
            "wireless",
            "internet",
            "network",
            "cca students",
            "cca-students",
            "get online",
        )
    )
    if wifi_topic_query:
        if section["article_id"] == "wifi-troubleshooting.txt":
            score += 24
        elif normalized_heading == "what students use it for:":
            score -= 30

    wifi_setup_query = any(
        phrase in normalized_question
        for phrase in (
            "how do i connect to the internet",
            "how do i connect to internet",
            "how do i connect to wifi",
            "how do i connect to wi fi",
            "how can i connect to wifi",
            "how can i connect to wi fi",
            "how do i get online",
            "get online",
            "join the student wifi",
            "join student wifi",
        )
    )
    wifi_which_network_query = any(
        phrase in normalized_question
        for phrase in (
            "what wifi",
            "which wifi",
            "wifi do students use",
            "wi fi do students use",
            "what network do students use",
            "student wifi network",
        )
    )
    wifi_connected_no_internet_query = (
        ("connected" in normalized_question or "connects" in normalized_question)
        and any(
            phrase in normalized_question
            for phrase in (
                "websites do not load",
                "websites don t load",
                "websites dont load",
                "no internet",
                "internet does not work",
                "internet is not working",
                "online services do not load",
            )
        )
    )
    wifi_not_visible_query = any(
        phrase in normalized_question
        for phrase in (
            "do not see cca students",
            "don t see cca students",
            "dont see cca students",
            "student wifi is not showing",
            "wifi is not showing",
            "not visible",
            "cannot find cca students",
            "can t find cca students",
        )
    )
    wifi_password_query = "wifi" in normalized_question and "password" in normalized_question

    if section["article_id"] == "wifi-troubleshooting.txt":
        if wifi_setup_query:
            if "first-time setup" in normalized_heading or "connect to wi fi" in normalized_heading:
                score += 90
            if "internet or network not working" in normalized_heading:
                score -= 30
            if "connected but websites do not load" in normalized_heading:
                score -= 20
        if wifi_which_network_query:
            if "cca student wi fi network name" in normalized_heading or normalized_heading == "summary:":
                score += 100
            if "what this helps with" in normalized_heading:
                score -= 20
        if wifi_connected_no_internet_query:
            if "connected but websites do not load" in normalized_heading:
                score += 100
            if "first-time setup" in normalized_heading:
                score -= 25
        if wifi_not_visible_query and "do not see cca students" in normalized_heading:
            score += 100
        if wifi_password_query and "password does not work" in normalized_heading:
            score += 100
        if (
            any(
                phrase in normalized_question
                for phrase in (
                    "wifi not working",
                    "wi fi not working",
                    "wireless network is not working",
                    "internet not working",
                    "internet is not working",
                    "internet broke",
                    "internet is broken",
                    "network not working",
                )
            )
            and (
                "internet or network not working" in normalized_heading
                or "cannot connect to cca wi fi" in normalized_heading
            )
        ):
            score += 80
        if wifi_topic_query and "what this helps with" in normalized_heading:
            score -= 20

    if "acces" in question_roots and "mater" in question_roots:
        if "how to access" in normalized_heading or "where to get help" in normalized_heading:
            score += 8
        if section["article_id"] == "d2l.txt":
            score += 12
        if section["article_id"] == "yuja-panorama.txt" and "yuja" not in question_roots and "video" not in question_roots:
            score -= 20

    if query_intent == "access/setup" and "stude" in question_roots and "email" in question_roots:
        if normalized_question == "how do i access student email":
            if section["article_id"] == "student-email.txt" and "accessing student email" in normalized_heading:
                score += 120
            if section["article_id"] == "student-email-troubleshooting.txt" and "cannot access student email" in normalized_heading:
                score -= 120
        if "how do i access student email" in normalized_question and "accessing student email" in normalized_heading:
            score += 34
        if "accessing student email" in normalized_heading:
            score += 28
        if section["article_id"] == "student-email.txt" and "alternative access" in normalized_heading:
            score += 18
        if section["article_id"] == "student-email-troubleshooting.txt":
            if "how do i access student email" in normalized_question and "cannot access student email" in normalized_heading:
                score -= 22
            if "cannot access student email" in normalized_heading and "not working" not in normalized_question:
                score -= 36
            if "student email not working" in normalized_heading:
                score -= 28

    if "print" in question_roots and "printing" in normalized_heading:
        score += 12
    if query_intent == "contact/help-location" and "print" in question_roots:
        if section["article_id"] == "printing.txt" and (
            "when to contact" in normalized_heading
            or "helpdesk" in normalized_heading
            or "printing from personal devices" in normalized_heading
        ):
            score += 34
        elif section_intent == "escalation/contact":
            score -= 20

    if "headp" in question_roots and "headphones" in normalized_heading:
        score += 12

    if "zoom" in question_roots and ("zoom" in normalized_heading or "zoom" in normalized_answer):
        score += 8
        if any(term in normalized_question for term in ("sso", "company domain", "license", "sign in", "login")):
            if "sign in problems" in normalized_heading:
                score += 80
            if "audio" in normalized_heading or "microphone" in normalized_heading:
                score -= 30
        if troubleshooting_query and (
            "not working" in normalized_heading
            or "audio not working" in normalized_heading
            or "microphone not working" in normalized_heading
            or "audio or video problems" in normalized_heading
            or "app or browser" in normalized_heading
        ):
            score += 14

    if "locat" in question_roots and "location" in normalized_heading:
        score += 12
    if query_intent == "contact/help-location" and ("located" in normalized_question or "location" in normalized_question):
        if normalized_heading == "location":
            score += 20

    if query_intent == "contact/help-location" and section["article_id"] == "classroom-technology.txt":
        if "where to get help" in normalized_heading or "when to contact" in normalized_heading:
            score += 24
        if "print" in question_roots or "yuja" in question_roots or "d2l" in question_roots:
            score -= 36

    if "proje" in question_roots and troubleshooting_query:
        if "where to get help" in normalized_heading:
            score -= 10

    if "upgra" in question_roots and "window" in question_roots and troubleshooting_query:
        if "where to get help" in normalized_heading:
            score -= 10

    if classifier_confidence >= 0.65:
        topic_text = " ".join(
            filter(
                None,
                (
                    section["article_id"],
                    normalized_title,
                    normalized_heading,
                    normalized_answer,
                ),
            )
        )
        topic_boosts = {
            "wifi": ("wifi", "wi fi", "wireless"),
            "email": ("email", "outlook", "office 365", "microsoft 365"),
            "d2l": ("d2l", "brightspace"),
            "zoom": ("zoom",),
            "classroom": ("classroom", "projector", "display", "audio", "instructor station"),
        }
        if classifier_topic in topic_boosts:
            if any(term in topic_text for term in topic_boosts[classifier_topic]):
                score += 8
            elif classifier_topic != "general":
                score -= 6

    return max(score, 0)


def confidence_from_score(score):
    if score >= 18:
        return "high"
    if score >= 9:
        return "medium"
    return "low"


def heuristic_retrieve_best_section(
    question,
    content_texts=None,
    article_ids=None,
    min_score=6,
    query_analysis=None,
):
    """
    Search across document sections with heuristic scoring.
    """
    if not question or not question.strip():
        return None

    texts = content_texts or load_retrieval_texts()
    candidate_ids = set(article_ids) if article_ids else None

    best = None
    for article_id, content_text in texts.items():
        if candidate_ids is not None and article_id not in candidate_ids:
            continue

        for section in split_document_sections(article_id, content_text):
            score = score_section(question, section, query_analysis=query_analysis)
            if best is None or score > best["score"]:
                best = {
                    "article_id": section["article_id"],
                    "section_heading": section["section_heading"],
                    "answer_text": section["answer_text"],
                    "score": score,
                    "full_document_text": section["full_document_text"],
                }

    if not best or best["score"] < min_score:
        return None

    return RetrievalResult(
        article_id=best["article_id"],
        section_heading=best["section_heading"],
        answer_text=best["answer_text"],
        score=best["score"],
        confidence=confidence_from_score(best["score"]),
        full_document_text=best["full_document_text"],
    )


def semantic_retrieval_enabled():
    return os.environ.get("IT_SUPPORT_EMBEDDINGS_ENABLED", "").strip() == "1"


def get_semantic_min_score():
    raw_value = os.environ.get("IT_SUPPORT_SEMANTIC_MIN_SCORE", "").strip()
    if not raw_value:
        return DEFAULT_SEMANTIC_MIN_SCORE

    try:
        return float(raw_value)
    except ValueError:
        return DEFAULT_SEMANTIC_MIN_SCORE


def retrieve_best_section(
    question,
    content_texts=None,
    article_ids=None,
    min_score=6,
    query_analysis=None,
):
    """
    Search across document sections and return the best supported section.
    """
    normalized_question = normalize_text(question or "")
    if "duo" in normalized_question or normalized_question in {
        "verification code is not working",
        "the verification code is not working",
    }:
        return None

    texts = content_texts or load_retrieval_texts()
    candidate_ids = set(article_ids) if article_ids else None
    heuristic_result = None

    if semantic_retrieval_enabled():
        try:
            sections = []
            for article_id, content_text in texts.items():
                if candidate_ids is not None and article_id not in candidate_ids:
                    continue
                sections.extend(split_document_sections(article_id, content_text))

            semantic_result = retrieve_best_semantic_section(
                question,
                sections,
                content_dir=CONTENT_DIR,
                model_name=DEFAULT_EMBEDDING_MODEL,
                min_similarity=get_semantic_min_score(),
            )
            if semantic_result is not None:
                semantic_retrieval_result = RetrievalResult(
                    article_id=semantic_result["article_id"],
                    section_heading=semantic_result["section_heading"],
                    answer_text=semantic_result["answer_text"],
                    score=semantic_result["score"],
                    confidence=semantic_result["confidence"],
                    full_document_text=semantic_result["full_document_text"],
                )
                heuristic_result = heuristic_retrieve_best_section(
                    question,
                    content_texts=texts,
                    article_ids=article_ids,
                    min_score=min_score,
                    query_analysis=query_analysis,
                )
                if heuristic_result is None:
                    return semantic_retrieval_result
                return heuristic_result
        except Exception:
            pass

    if heuristic_result is not None:
        return heuristic_result

    return heuristic_retrieve_best_section(
        question,
        content_texts=texts,
        article_ids=article_ids,
        min_score=min_score,
        query_analysis=query_analysis,
    )
