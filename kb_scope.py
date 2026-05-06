from dataclasses import dataclass
from pathlib import Path
import re


CONTENT_DIR = Path(__file__).parent / "content"


@dataclass(frozen=True)
class ArticleScope:
    article_id: str
    audience: str
    visibility: str
    safe_for_student: bool
    topic: str
    is_internal: bool


def article_id_for_path(path, content_dir=CONTENT_DIR):
    return path.relative_to(content_dir).as_posix()


def iter_content_paths(content_dir=CONTENT_DIR):
    return sorted(content_dir.rglob("*.txt"))


def parse_article_metadata(content_text):
    """
    Parse simple top-level article metadata without depending on guide format.
    """
    metadata = {}
    current_key = None
    for raw_line in (content_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            current_key = None
            continue

        field_match = re.match(
            r"^-?\s*(TITLE|AUDIENCE|VISIBILITY|TOPIC|SAFE_FOR_STUDENT|STATUS):\s*(.*)$",
            line,
            flags=re.IGNORECASE,
        )
        if field_match:
            current_key = field_match.group(1).upper()
            value = field_match.group(2).strip()
            if value:
                metadata[current_key] = value
            continue

        if current_key and current_key not in metadata:
            metadata[current_key] = line
            current_key = None

    return metadata


def infer_article_scope(article_id, content_text):
    metadata = parse_article_metadata(content_text)
    audience = metadata.get("AUDIENCE", "").strip().lower()
    visibility = metadata.get("VISIBILITY", "").strip().lower()
    safe_value = metadata.get("SAFE_FOR_STUDENT", "").strip().lower()
    topic = metadata.get("TOPIC", "").strip().lower()
    status = metadata.get("STATUS", "").strip().lower()

    nested_article = "/" in article_id
    draft_import = "draft" in status or "source document imported" in status
    internal_audience = any(
        term in audience
        for term in (
            "it_staff",
            "it staff",
            "student worker",
            "intern",
            "temporary staff",
        )
    )

    if not visibility:
        visibility = "internal" if nested_article or draft_import or internal_audience else "public"

    if not safe_value:
        safe_for_student = visibility == "public" and not nested_article and not internal_audience
    else:
        safe_for_student = safe_value in {"1", "true", "yes", "y"}

    is_internal = visibility == "internal" or not safe_for_student
    if not audience:
        audience = "it_staff" if is_internal else "student"

    return ArticleScope(
        article_id=article_id,
        audience=audience,
        visibility=visibility,
        safe_for_student=safe_for_student,
        topic=topic,
        is_internal=is_internal,
    )


def load_scoped_content_texts(include_internal=False, internal_only=False, content_dir=CONTENT_DIR):
    texts = {}
    for path in iter_content_paths(content_dir):
        article_id = article_id_for_path(path, content_dir=content_dir)
        text = path.read_text(encoding="utf-8")
        scope = infer_article_scope(article_id, text)

        if internal_only:
            if scope.is_internal:
                texts[article_id] = text
            continue

        if include_internal or (scope.visibility == "public" and scope.safe_for_student):
            texts[article_id] = text

    return texts


def get_article_scope(article_id, content_text):
    return infer_article_scope(article_id or "", content_text or "")
