from dataclasses import dataclass
from pathlib import Path

from router import expand_query_tokens, normalize_text, tokenize_text

CONTENT_DIR = Path(__file__).parent / "content"
LOW_VALUE_TOKENS = {
    "a", "an", "and", "are", "can", "do", "for", "get", "help", "how",
    "i", "if", "in", "is", "it", "me", "my", "need", "not", "of", "on",
    "or", "the", "to", "we", "what", "where", "with", "working", "you",
}
ACTIONABLE_QUERY_TOKENS = {
    "access", "assignment", "assignments", "borrow", "calculator", "class",
    "connect", "course", "courses", "email", "find", "get", "join", "laptop",
    "link", "log", "login", "materials", "meeting", "password", "print",
    "projector", "quiz", "quizzes", "reset", "submit", "video", "wifi",
    "windows", "wireless", "yuja", "zoom",
}
GENERIC_SECTION_HEADINGS = {
    "what this is:",
    "what students use it for:",
    "things to know:",
}
TROUBLESHOOTING_PHRASES = {
    "can t", "cannot", "unable", "not working", "locked", "issue", "problem",
    "problems", "is not working", "won t",
}


@dataclass
class RetrievalResult:
    article_id: str
    section_heading: str
    answer_text: str
    score: int
    confidence: str
    full_document_text: str


def load_retrieval_texts():
    """
    Load all text files from content/ for section retrieval.
    """
    texts = {}
    for path in CONTENT_DIR.glob("*.txt"):
        texts[path.name] = path.read_text(encoding="utf-8")
    return texts


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


def score_section(question, section):
    normalized_question = normalize_text(question)
    normalized_heading = normalize_text(section["section_heading"])
    normalized_title = normalize_text(section["document_title"])
    normalized_answer = normalize_text(section["answer_text"])
    weighted_tokens = build_weighted_query_tokens(question)
    question_roots = {canonicalize_token(token) for token in tokenize_text(question) if token not in LOW_VALUE_TOKENS}
    answer_token_counts = build_token_counts(section["answer_text"])
    heading_token_counts = build_token_counts(section["section_heading"])
    title_token_counts = build_token_counts(section["document_title"])

    if not weighted_tokens:
        return 0

    score = 0
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
        if "where to get help" in normalized_heading or "where to go for help" in normalized_heading:
            score += 10
        if "contact" in normalized_answer:
            score += 6

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

    if "acces" in question_roots and "mater" in question_roots:
        if "how to access" in normalized_heading or "where to get help" in normalized_heading:
            score += 8
        if section["article_id"] == "yuja-panorama.txt" and "yuja" not in question_roots and "video" not in question_roots:
            score -= 12

    if "print" in question_roots and "printing" in normalized_heading:
        score += 12

    if "headp" in question_roots and "headphones" in normalized_heading:
        score += 12

    if "zoom" in question_roots and ("zoom" in normalized_heading or "zoom" in normalized_answer):
        score += 8

    if "locat" in question_roots and "location" in normalized_heading:
        score += 12

    if "proje" in question_roots and troubleshooting_query:
        if "where to get help" in normalized_heading:
            score += 10

    if "upgra" in question_roots and "window" in question_roots and troubleshooting_query:
        if "where to get help" in normalized_heading:
            score += 10

    return max(score, 0)


def confidence_from_score(score):
    if score >= 18:
        return "high"
    if score >= 9:
        return "medium"
    return "low"


def retrieve_best_section(question, content_texts=None, article_ids=None, min_score=6):
    """
    Search across document sections and return the best supported section.
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
            score = score_section(question, section)
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
