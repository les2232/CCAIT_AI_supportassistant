#!/usr/bin/env python3
import argparse
import sys

from app import resolve_question
from pilot_eval_cases import PILOT_EVAL_CASES
from response_builder import (
    build_additional_troubleshooting_steps,
    detect_disambiguation_options,
    extract_escalation_text,
    extract_step_items,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate realistic pilot queries against the current guided support flow."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any hard failures are found.",
    )
    return parser.parse_args()


def classify_warning(question, result, guided_steps):
    warnings = []
    lowered = (question or "").lower()
    section = (result.get("section_heading") or "").lower()

    if not guided_steps:
        warnings.append("confusing guided steps: no steps generated")

    if ("where is" in lowered or "where do i" in lowered or "who can help" in lowered) and len(guided_steps) > 5:
        warnings.append("confusing guided steps: support/contact question produced a long procedure")

    if ("location" in lowered or "where is" in lowered) and "location" not in section:
        warnings.append("vague answer: location-style query matched a non-location section")

    return warnings


def main():
    args = parse_args()
    failures = []
    warnings = []

    print("Pilot query evaluation")
    print("=" * 72)
    print("Dataset: realistic student and faculty support questions")

    for case in PILOT_EVAL_CASES:
        question = case["question"]
        expected_behavior = case["expected_behavior"]
        notes = case["notes"]

        options = detect_disambiguation_options(question)
        if expected_behavior == "disambiguation":
            actual_labels = [option["label"] for option in options]
            expected_labels = case["expected_options"]
            if actual_labels != expected_labels:
                failures.append(
                    {
                        "question": question,
                        "category": "poor disambiguation",
                        "expected": expected_labels,
                        "actual": actual_labels,
                        "notes": notes,
                    }
                )
                continue
            print(f"[PASS] {question!r} -> disambiguation")
            continue

        if options:
            failures.append(
                {
                    "question": question,
                    "category": "poor disambiguation",
                    "expected": "direct guidance",
                    "actual": [option["label"] for option in options],
                    "notes": notes,
                }
            )
            continue

        result = resolve_question(question)
        actual_article = result.get("source_name")
        expected_article = case["expected_article"]
        if actual_article != expected_article:
            failures.append(
                {
                    "question": question,
                    "category": "wrong article",
                    "expected": expected_article,
                    "actual": actual_article,
                    "notes": notes,
                }
            )
            continue

        rendered_response = result.get("rendered_response")
        if not rendered_response or not rendered_response.strip():
            failures.append(
                {
                    "question": question,
                    "category": "vague answer",
                    "expected": "non-empty guided answer",
                    "actual": rendered_response,
                    "notes": notes,
                }
            )
            continue

        guided_steps = extract_step_items(
            rendered_response,
            content_text=result.get("full_document_text"),
            question=question,
            section_heading=result.get("section_heading"),
        )
        if not guided_steps:
            failures.append(
                {
                    "question": question,
                    "category": "confusing guided steps",
                    "expected": "at least one guided step",
                    "actual": guided_steps,
                    "notes": notes,
                }
            )
            continue

        escalation_text = result.get("escalation_text") or extract_escalation_text(result.get("full_document_text"))
        if not escalation_text:
            failures.append(
                {
                    "question": question,
                    "category": "missing escalation",
                    "expected": "escalation guidance",
                    "actual": None,
                    "notes": notes,
                }
            )
            continue

        followup_steps = build_additional_troubleshooting_steps(
            question=question,
            source_name=result.get("source_name"),
            content_text=result.get("full_document_text"),
        )
        if not followup_steps:
            failures.append(
                {
                    "question": question,
                    "category": "confusing guided steps",
                    "expected": "follow-up troubleshooting steps",
                    "actual": followup_steps,
                    "notes": notes,
                }
            )
            continue

        case_warnings = classify_warning(question, result, guided_steps)
        for warning in case_warnings:
            warnings.append(
                {
                    "question": question,
                    "category": warning,
                    "article": actual_article,
                    "notes": notes,
                }
            )

        print(f"[PASS] {question!r} -> {actual_article}")

    print()
    print(f"Total cases: {len(PILOT_EVAL_CASES)}")
    print(f"Passed:      {len(PILOT_EVAL_CASES) - len(failures)}")
    print(f"Failed:      {len(failures)}")
    print(f"Warnings:    {len(warnings)}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure['question']!r}")
            print(f"  category: {failure['category']}")
            print(f"  expected: {failure['expected']}")
            print(f"  actual:   {failure['actual']}")
            print(f"  notes:    {failure['notes']}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning['question']!r}")
            print(f"  category: {warning['category']}")
            print(f"  article:  {warning['article']}")
            print(f"  notes:    {warning['notes']}")

    if args.strict and failures:
        sys.exit(1)

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
