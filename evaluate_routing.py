import argparse

from router import legacy_select_response, load_content_texts, select_response

CASES = [
    ("How do I reset my password?", "password-reset.txt"),
    ("My MFA is not working", "password-reset.txt"),
    ("My account is locked", "password-reset.txt"),
    ("I can't get into my online class", "d2l.txt"),
    ("Where do I find my assignments?", "d2l.txt"),
    ("Where do I submit assignments?", "d2l.txt"),
    ("I need help with Zoom", "online-blended-learning.txt"),
    ("How do I access student email?", "student-email.txt"),
    ("Can I borrow a calculator?", "student-laptops-calculators.txt"),
    ("Wi-Fi keeps dropping on my laptop", "wifi-troubleshooting.txt"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare legacy routing against the upgraded routing."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a non-zero status code if the upgraded router misses an expected route.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    content_texts = load_content_texts()
    failures = []

    print("Routing evaluation")
    print("=" * 72)

    for question, expected in CASES:
        legacy_article, _ = legacy_select_response(question, content_texts)
        upgraded_article, _ = select_response(question, content_texts)
        improved = legacy_article != expected and upgraded_article == expected
        passed = upgraded_article == expected

        print(f"Question: {question}")
        print(f"  Expected:  {expected}")
        print(f"  Legacy:    {legacy_article}")
        print(f"  Upgraded:  {upgraded_article}")
        print(f"  Result:    {'PASS' if passed else 'FAIL'}")
        if improved:
            print("  Change:    upgraded router fixed a legacy miss")
        print()

        if not passed:
            failures.append((question, expected, upgraded_article))

    print("=" * 72)
    print(f"Total cases: {len(CASES)}")
    print(f"Passed:      {len(CASES) - len(failures)}")
    print(f"Failed:      {len(failures)}")

    if failures:
        print("\nFailed cases:")
        for question, expected, actual in failures:
            print(f"- {question}")
            print(f"  expected: {expected}")
            print(f"  actual:   {actual}")

    if args.strict and failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
