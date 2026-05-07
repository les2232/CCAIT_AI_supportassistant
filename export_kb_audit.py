from pathlib import Path

from kb_scope import (
    article_id_for_path,
    content_namespace_for_path,
    get_article_scope,
    iter_content_paths,
)
from response_builder import GUIDE_FIELD_NAMES, parse_guide_content, parse_section_map


ROOT_DIR = Path(__file__).parent
CONTENT_DIR = ROOT_DIR / "content"
OUTPUT_PATH = ROOT_DIR / "docs" / "manual-kb-review.md"


def read_source_label(content_text):
    for line in content_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("SOURCE:"):
            return stripped.partition(":")[2].strip()
    return ""


def format_scalar(value):
    if not value:
        return "_Not provided_"
    return value


def format_tags(tags):
    if not tags:
        return "_Not provided_"
    return ", ".join(tags)


def format_field_items(items):
    if not items:
        return ["- _Not provided_"]
    return [f"- `{item}`" for item in items]


def build_article_section(path):
    content_text = path.read_text(encoding="utf-8")
    article_id = article_id_for_path(path)
    guide = parse_guide_content(content_text)
    section_map = parse_section_map(content_text)
    source_label = read_source_label(content_text)

    lines = [
        f"## {article_id}",
        "",
        f"- File name: `{article_id}`",
        f"- SOURCE: {format_scalar(source_label)}",
        f"- TITLE: {format_scalar((guide.get('TITLE') or '').strip())}",
        f"- AUDIENCE: {format_scalar((guide.get('AUDIENCE') or '').strip())}",
        f"- TAGS: {format_tags(guide.get('TAGS') or [])}",
        "",
        "### Guide Fields",
        "",
    ]

    for field_name in GUIDE_FIELD_NAMES:
        value = guide.get(field_name)
        if field_name in {"TITLE", "AUDIENCE"}:
            lines.append(f"- `{field_name}`: {format_scalar((value or '').strip())}")
        elif field_name == "TAGS":
            lines.append(f"- `{field_name}`: {format_tags(value or [])}")
        else:
            lines.append(f"- `{field_name}`:")
            lines.extend(format_field_items(value or []))

    lines.extend(
        [
            "",
            "### Section Headings",
            "",
        ]
    )

    if section_map:
        for heading in section_map:
            lines.append(f"- `{heading}`")
    else:
        lines.append("- _No section headings found_")

    lines.extend(
        [
            "",
            "### Audit",
            "",
            "- Claims to verify:",
            "  - ",
            "- Source of truth:",
            "  - ",
            "- Status:",
            "  - ",
            "- Decision:",
            "  - ",
            "- Notes:",
            "  - ",
            "",
            "---",
            "",
        ]
    )

    return "\n".join(lines)


def build_document():
    sections = []
    for path in iter_content_paths(CONTENT_DIR):
        content_text = path.read_text(encoding="utf-8")
        article_id = article_id_for_path(path)
        scope = get_article_scope(
            article_id,
            content_text,
            namespace=content_namespace_for_path(path),
        )
        if scope.is_internal:
            continue
        sections.append(build_article_section(path))

    return "\n".join(
        [
            "# Manual KB Review",
            "",
            "Generated from public KB articles under `content/public/` by `export_kb_audit.py`.",
            "",
            "Use this document to review article claims, confirm sources of truth, and record revision decisions without editing the source articles directly.",
            "",
            "---",
            "",
            *sections,
        ]
    )


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_document(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    raise SystemExit(main())
