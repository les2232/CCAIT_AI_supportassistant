#!/usr/bin/env python3
import os
import sys
from contextlib import contextmanager

from flask import template_rendered

from app import app
from kb_scope import load_scoped_content_texts
from support_service import resolve_question


STUDENT_LEAKAGE_CASES = [
    "what is the printer server path",
    "ID Flow database issue",
    "when do I escalate this IT ticket",
    "classroom internal troubleshooting checklist",
    "Zoom SSO login",
]

FORBIDDEN_STUDENT_TERMS = (
    "ccadprint01",
    "select a shared printer by name",
    "ticket notes to include",
    "user/requester",
    "escalate if",
    "cccs-edu",
)

INTERNAL_CASES = [
    ("how do I map a printer", "ccadprint01"),
    ("Zoom SSO login", "CCCS-EDU"),
    ("student Microsoft 365 MFA setup SOP", "TICKET NOTES TO INCLUDE"),
]


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


def evaluate_loader_scope(failures):
    public_texts = load_scoped_content_texts()
    internal_texts = load_scoped_content_texts(internal_only=True)

    if any("/" in article_id for article_id in public_texts):
        failures.append(("loader public scope", f"nested internal article loaded publicly: {sorted(public_texts)}"))
    for expected in (
        "printing/map-network-printer.txt",
        "zoom/zoom-sso-login.txt",
        "mfa/student-microsoft-365-mfa.txt",
        "software/pdf-digital-signature-acrobat.txt",
    ):
        if expected not in internal_texts:
            failures.append(("loader internal scope", f"missing internal article: {expected}"))
    if not failures:
        print("[PASS] scoped loader separates public and internal articles")


def evaluate_student_leakage(failures):
    previous = os.environ.pop("ENABLE_INTERNAL_KB", None)
    previous_allowed = os.environ.pop("INTERNAL_KB_ALLOWED_USERS", None)
    try:
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["logged_in"] = True
                sess["username"] = "student-view"

            for query in STUDENT_LEAKAGE_CASES:
                with captured_templates(app) as templates:
                    response = client.post("/", data={"question": query}, follow_redirects=True)

                body = response.get_data(as_text=True).lower()
                if response.status_code != 200:
                    failures.append((query, f"unexpected status code: {response.status_code}"))
                    continue
                if not templates:
                    failures.append((query, "no template context captured"))
                    continue

                _, context = templates[-1]
                if context.get("internal_notes"):
                    failures.append((query, "student response included internal notes"))
                    continue
                if context.get("source_name") and "/" in context.get("source_name"):
                    failures.append((query, f"student response used internal source: {context.get('source_name')}"))
                    continue
                leaked = [term for term in FORBIDDEN_STUDENT_TERMS if term in body]
                if leaked:
                    failures.append((query, f"student response leaked internal terms: {leaked}"))
                    continue
                print(f"[PASS] student scope blocks internal leakage for {query!r}")
    finally:
        if previous is not None:
            os.environ["ENABLE_INTERNAL_KB"] = previous
        if previous_allowed is not None:
            os.environ["INTERNAL_KB_ALLOWED_USERS"] = previous_allowed


def evaluate_student_cannot_force_internal_mode(failures):
    previous_enable = os.environ.get("ENABLE_INTERNAL_KB")
    previous_allowed = os.environ.get("INTERNAL_KB_ALLOWED_USERS")
    previous_default = os.environ.get("INTERNAL_KB_DEFAULT")
    os.environ["ENABLE_INTERNAL_KB"] = "1"
    os.environ["INTERNAL_KB_ALLOWED_USERS"] = "staff-view"
    os.environ.pop("INTERNAL_KB_DEFAULT", None)
    try:
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["logged_in"] = True
                sess["username"] = "student-view"
            with captured_templates(app) as templates:
                response = client.post(
                    "/",
                    data={"question": "how do I map a printer", "internal_mode": "1"},
                    follow_redirects=True,
                )

            body = response.get_data(as_text=True).lower()
            if response.status_code != 200:
                failures.append(("student forced internal mode", f"unexpected status code: {response.status_code}"))
            elif not templates:
                failures.append(("student forced internal mode", "no template context captured"))
            else:
                _, context = templates[-1]
                leaked = [term for term in FORBIDDEN_STUDENT_TERMS if term in body]
                if context.get("internal_notes") or leaked:
                    failures.append(
                        (
                            "student forced internal mode",
                            f"unauthorized internal notes visible; leaked terms: {leaked}",
                        )
                    )
                else:
                    print("[PASS] student cannot force internal mode with form flag")
    finally:
        if previous_enable is None:
            os.environ.pop("ENABLE_INTERNAL_KB", None)
        else:
            os.environ["ENABLE_INTERNAL_KB"] = previous_enable
        if previous_allowed is None:
            os.environ.pop("INTERNAL_KB_ALLOWED_USERS", None)
        else:
            os.environ["INTERNAL_KB_ALLOWED_USERS"] = previous_allowed
        if previous_default is None:
            os.environ.pop("INTERNAL_KB_DEFAULT", None)
        else:
            os.environ["INTERNAL_KB_DEFAULT"] = previous_default


def evaluate_internal_mode(failures):
    previous_enable = os.environ.get("ENABLE_INTERNAL_KB")
    previous_allowed = os.environ.get("INTERNAL_KB_ALLOWED_USERS")
    previous_default = os.environ.get("INTERNAL_KB_DEFAULT")
    os.environ["ENABLE_INTERNAL_KB"] = "1"
    os.environ["INTERNAL_KB_ALLOWED_USERS"] = "staff-view"
    os.environ.pop("INTERNAL_KB_DEFAULT", None)
    try:
        for query, expected_text in INTERNAL_CASES:
            result = resolve_question(query, include_internal=True)
            notes = result.get("internal_notes") or {}
            note_text = " ".join(
                str(notes.get(key) or "")
                for key in ("source_name", "section_heading", "content")
            )
            if expected_text.lower() not in note_text.lower():
                failures.append((query, f"internal notes missing {expected_text!r}: {notes}"))
                continue
            if result.get("source_name") and "/" in result.get("source_name"):
                failures.append((query, "internal source replaced student-facing source"))
                continue
            print(f"[PASS] internal retrieval available for {query!r}")

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["logged_in"] = True
                sess["username"] = "staff-view"
            with captured_templates(app) as templates:
                response = client.post(
                    "/",
                    data={"question": "how do I map a printer", "internal_mode": "1"},
                    follow_redirects=True,
                )
            body = response.get_data(as_text=True)
            if response.status_code != 200:
                failures.append(("internal UI", f"unexpected status code: {response.status_code}"))
            elif not templates:
                failures.append(("internal UI", "no template context captured"))
            elif "Internal IT Notes" not in body or "ccadprint01" not in body:
                failures.append(("internal UI", "internal notes panel did not render printer SOP details"))
            else:
                print("[PASS] internal mode renders Internal IT Notes panel")
    finally:
        if previous_enable is None:
            os.environ.pop("ENABLE_INTERNAL_KB", None)
        else:
            os.environ["ENABLE_INTERNAL_KB"] = previous_enable
        if previous_allowed is None:
            os.environ.pop("INTERNAL_KB_ALLOWED_USERS", None)
        else:
            os.environ["INTERNAL_KB_ALLOWED_USERS"] = previous_allowed
        if previous_default is None:
            os.environ.pop("INTERNAL_KB_DEFAULT", None)
        else:
            os.environ["INTERNAL_KB_DEFAULT"] = previous_default


def main():
    failures = []
    print("KB scope evaluation")
    print("=" * 72)
    evaluate_loader_scope(failures)
    evaluate_student_leakage(failures)
    evaluate_student_cannot_force_internal_mode(failures)
    evaluate_internal_mode(failures)

    print()
    print(f"Failed: {len(failures)}")
    if failures:
        for query, error in failures:
            print(f"- {query!r}")
            print(f"  {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
