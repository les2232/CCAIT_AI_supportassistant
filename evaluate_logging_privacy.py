#!/usr/bin/env python3
from logging_store import redact_sensitive_log_text


CASES = [
    {
        "name": "password, code, student id, email, and phone are redacted",
        "input": (
            "My password is Hunter2, MFA code 123456, student id S12345678, "
            "email alex.student@example.edu, phone 303-555-1212"
        ),
        "must_not_contain": [
            "Hunter2",
            "123456",
            "S12345678",
            "alex.student@example.edu",
            "303-555-1212",
        ],
        "must_contain": [
            "[redacted-password]",
            "[redacted-code]",
            "[redacted-student-id]",
            "[redacted-email]",
            "[redacted-phone]",
        ],
    },
    {
        "name": "feedback comment redaction keeps non-sensitive context",
        "input": "Please call me at (303) 555-1212 about my email problem.",
        "must_not_contain": ["(303) 555-1212"],
        "must_contain": ["[redacted-phone]", "email problem"],
    },
    {
        "name": "none stays none",
        "input": None,
        "expected": None,
    },
]


def run_case(case):
    redacted = redact_sensitive_log_text(case["input"])
    if "expected" in case:
        assert redacted == case["expected"], (
            f"{case['name']}: expected {case['expected']!r}, got {redacted!r}"
        )
        return

    for value in case["must_not_contain"]:
        assert value not in redacted, f"{case['name']}: did not redact {value!r}"
    for value in case["must_contain"]:
        assert value in redacted, f"{case['name']}: missing marker/context {value!r}"


def main():
    failures = []
    for case in CASES:
        try:
            run_case(case)
            print(f"PASS {case['name']}")
        except AssertionError as exc:
            failures.append(str(exc))
            print(f"FAIL {case['name']}: {exc}")

    if failures:
        print()
        print(f"{len(failures)} logging privacy case(s) failed.")
        raise SystemExit(1)

    print()
    print(f"Logging privacy evaluation passed: {len(CASES)} cases.")


if __name__ == "__main__":
    main()
