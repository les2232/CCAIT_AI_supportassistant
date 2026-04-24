import argparse

from router import legacy_select_response, load_content_texts, select_response
from routing_eval_cases import ROUTING_EVAL_CASES


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
    improvements = []
    category_totals = {}
    category_failures = {}

    print("Routing evaluation")
    print("=" * 72)

    for case in ROUTING_EVAL_CASES:
        category = case["category"]
        question = case["question"]
        expected = case["expected"]

        legacy_article, _ = legacy_select_response(question, content_texts)
        upgraded_article, _ = select_response(question, content_texts)
        improved = legacy_article != expected and upgraded_article == expected
        passed = upgraded_article == expected

        category_totals[category] = category_totals.get(category, 0) + 1

        if not passed:
            failures.append((category, question, expected, upgraded_article, legacy_article))
            category_failures[category] = category_failures.get(category, 0) + 1
        elif improved:
            improvements.append((category, question, expected, legacy_article))

    print("=" * 72)
    print("Dataset: representative test cases derived from current content and routing")
    print(f"Total cases: {len(ROUTING_EVAL_CASES)}")
    print(f"Passed:      {len(ROUTING_EVAL_CASES) - len(failures)}")
    print(f"Failed:      {len(failures)}")
    print(f"Improved:    {len(improvements)}")

    print("\nBy category:")
    for category in sorted(category_totals):
        total = category_totals[category]
        failed = category_failures.get(category, 0)
        passed = total - failed
        print(f"- {category}: {passed}/{total} passed")

    if failures:
        print("\nFailed cases:")
        for category, question, expected, actual, legacy in failures:
            print(f"- [{category}] {question!r}")
            print(f"  expected: {expected}")
            print(f"  upgraded: {actual}")
            print(f"  legacy:   {legacy}")

    if improvements:
        print("\nLegacy misses fixed by upgraded router:")
        for category, question, expected, legacy in improvements:
            print(f"- [{category}] {question!r} -> {expected} (legacy: {legacy})")

    if args.strict and failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
