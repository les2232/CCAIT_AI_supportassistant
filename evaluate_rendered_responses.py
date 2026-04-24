#!/usr/bin/env python3
import re
import sys
from contextlib import contextmanager

from flask import template_rendered

from app import app


QUERIES = [
    "Classroom display won’t turn on",
    "Projector has no signal",
    "Audio not working in classroom",
]

METADATA_PATTERNS = (
    "TITLE:",
    "AUDIENCE:",
    "TAGS:",
    "CONTEXT:",
    "STEPS:",
    "IF NOT FIXED:",
    "ESCALATE:",
)


@contextmanager
def captured_templates(flask_app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, flask_app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, flask_app)


def contains_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("display", "projector", "input", "source", "laptop", "computer", "power")
    return any(keyword in joined for keyword in keywords)


def is_heading_only(step):
    stripped = step.strip()
    if not stripped:
        return True
    return stripped.endswith(":") and len(stripped.split()) <= 12


def main():
    failures = []

    print("Rendered response evaluation")
    print("=" * 72)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "testuser"

        for query in QUERIES:
            with captured_templates(app) as templates:
                response = client.post("/", data={"question": query}, follow_redirects=True)

            if response.status_code != 200:
                failures.append((query, f"unexpected status code: {response.status_code}"))
                continue

            if not templates:
                failures.append((query, "no template context captured"))
                continue

            _, context = templates[-1]
            source_name = context.get("source_name")
            section_heading = context.get("section_heading")
            guided_steps = context.get("guided_steps") or []
            escalation_text = context.get("escalation_text") or ""

            if source_name != "classroom-technology.txt":
                failures.append((query, f"wrong article: {source_name}"))
                continue

            if len(guided_steps) < 3:
                failures.append((query, f"too few guided steps: {guided_steps}"))
                continue

            if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                continue

            if all(is_heading_only(step) for step in guided_steps):
                failures.append((query, f"guided steps contain only headings: {guided_steps}"))
                continue

            if not contains_guidance(guided_steps):
                failures.append((query, f"guided steps missing display/projector/source guidance: {guided_steps}"))
                continue

            if not escalation_text.strip():
                failures.append((query, "missing escalation text"))
                continue

            print(f"[PASS] {query!r}")
            print(f"  article: {source_name}")
            print(f"  section: {section_heading}")
            print(f"  steps:   {guided_steps[:4]}")

    print()
    print(f"Total cases: {len(QUERIES)}")
    print(f"Passed:      {len(QUERIES) - len(failures)}")
    print(f"Failed:      {len(failures)}")

    if failures:
        print("\nFailures:")
        for query, error in failures:
            print(f"- {query!r}")
            print(f"  {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
