from pathlib import Path
import sys

from response_builder import (
    GUIDE_FIELD_NAMES,
    count_user_facing_steps,
    extract_escalation_text,
    heuristic_extract_step_items,
    is_guide_metadata_line,
    parse_guide_content,
    parse_section_map,
    resolve_guide_items,
    strip_guide_metadata_lines,
)


CONTENT_DIR = Path(__file__).parent / "content"


def heading_reference_errors(field_name, items, section_map):
    errors = []
    for item in items or []:
        reference = item.strip()
        if not reference:
            continue
        if reference.endswith(":") and reference not in section_map:
            errors.append(
                f"{field_name} references missing heading: {reference}"
            )
    return errors


def validate_file(path):
    content_text = path.read_text(encoding="utf-8")
    guide = parse_guide_content(content_text)
    section_map = parse_section_map(content_text)

    warnings = []
    errors = []

    is_guide_ready = any(field in guide for field in GUIDE_FIELD_NAMES)

    if not is_guide_ready:
        warnings.append("No structured guide fields found.")
        return warnings, errors

    missing_fields = [field for field in GUIDE_FIELD_NAMES if field not in guide]
    for field in missing_fields:
        errors.append(f"Missing guide field: {field}")

    for field in ("CONTEXT", "STEPS", "IF NOT FIXED", "ESCALATE"):
        errors.extend(heading_reference_errors(field, guide.get(field, []), section_map))

    title = (guide.get("TITLE") or "").strip()
    audience = (guide.get("AUDIENCE") or "").strip()
    tags = guide.get("TAGS") or []

    if not title:
        errors.append("TITLE is empty.")
    if not audience:
        errors.append("AUDIENCE is empty.")
    if not tags:
        errors.append("TAGS is empty.")

    steps = []
    resolved_step_blocks = resolve_guide_items(guide.get("STEPS", []), content_text)
    for resolved in resolved_step_blocks:
        if any(is_guide_metadata_line(line) for line in resolved.splitlines() if line.strip()):
            errors.append("STEPS resolves to metadata field labels instead of user-facing guidance.")
            break
        steps.extend(heuristic_extract_step_items(resolved))
    if not steps:
        errors.append("STEPS does not resolve to at least one usable step.")
    elif len(steps) < 2:
        errors.append("STEPS does not resolve to at least two user-facing troubleshooting steps.")

    total_user_facing_steps = sum(count_user_facing_steps(block) for block in resolved_step_blocks)
    if total_user_facing_steps < 2:
        errors.append("STEPS does not contain at least two real user-facing step lines.")

    escalation = extract_escalation_text(content_text)
    if not escalation or not escalation.strip():
        errors.append("ESCALATE does not resolve to any escalation text.")
    else:
        cleaned_escalation = strip_guide_metadata_lines(escalation)
        if not cleaned_escalation:
            errors.append("ESCALATE resolves only to metadata or heading labels.")
        elif all(
            line.strip().endswith(":") and len(line.strip().split()) <= 12
            for line in cleaned_escalation.splitlines()
            if line.strip()
        ):
            errors.append("ESCALATE resolves only to heading labels without contact guidance.")

    return warnings, errors


def main():
    files = sorted(CONTENT_DIR.glob("*.txt"))
    files_checked = 0
    passing_files = []
    warning_files = []
    error_files = []

    for path in files:
        files_checked += 1
        warnings, errors = validate_file(path)
        if errors:
            error_files.append((path.name, warnings, errors))
        elif warnings:
            warning_files.append((path.name, warnings))
        else:
            passing_files.append(path.name)

    print("Knowledge base validation")
    print("========================================================================")
    print(f"Files checked:  {files_checked}")
    print(f"Files passing:  {len(passing_files)}")
    print(f"Files warnings: {len(warning_files)}")
    print(f"Files errors:   {len(error_files)}")

    if passing_files:
        print("\nPassing files:")
        for name in passing_files:
            print(f"- {name}")

    if warning_files:
        print("\nFiles with warnings:")
        for name, warnings in warning_files:
            print(f"- {name}")
            for warning in warnings:
                print(f"  warning: {warning}")

    if error_files:
        print("\nFiles with errors:")
        for name, warnings, errors in error_files:
            print(f"- {name}")
            for warning in warnings:
                print(f"  warning: {warning}")
            for error in errors:
                print(f"  error: {error}")

    return 1 if error_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
