#!/usr/bin/env python3
import sys

from response_builder import detect_disambiguation_options


TEST_CASES = [
    {
        "query": "can't log in",
        "expected_labels": ["D2L", "Student email", "MyCCA", "Campus computer", "Wi-Fi", "MFA/Auth", "I'm not sure"],
    },
    {
        "query": "can't access my class",
        "expected_labels": ["D2L", "Email", "Zoom", "Course videos"],
    },
    {
        "query": "nothing is working",
        "expected_labels": ["Wi-Fi", "D2L", "Email", "Zoom", "I'm not sure"],
    },
    {
        "query": "can't open anything",
        "expected_labels": ["D2L", "Email", "Zoom", "Course videos", "I'm not sure"],
    },
    {
        "query": "problem with login",
        "expected_labels": ["D2L", "Student email", "MyCCA", "Campus computer", "Wi-Fi", "MFA/Auth", "I'm not sure"],
    },
    {
        "query": "it won't let me in",
        "expected_labels": ["D2L", "Student email", "MyCCA", "Campus computer", "Wi-Fi", "MFA/Auth", "I'm not sure"],
    },
    {
        "query": "MFA is not working",
        "expected_labels": ["Student Microsoft Authenticator", "Faculty/Staff Duo", "I'm not sure"],
    },
    {
        "query": "verification code is not working",
        "expected_labels": ["Student Microsoft Authenticator", "Faculty/Staff Duo", "I'm not sure"],
    },
    {
        "query": "Duo not working",
        "expected_labels": ["Student Microsoft Authenticator", "Faculty/Staff Duo", "I'm not sure"],
    },
]


def main():
    passed = 0
    failed = 0

    print("Disambiguation evaluation")
    print("=" * 72)

    for case in TEST_CASES:
        query = case["query"]
        expected = case["expected_labels"]
        actual = [option["label"] for option in detect_disambiguation_options(query)]
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {query!r}")
        print(f"  expected: {expected}")
        print(f"  actual:   {actual}")
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Total cases: {len(TEST_CASES)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
