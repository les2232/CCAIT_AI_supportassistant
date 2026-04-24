import argparse

from retrieval_eval_cases import RETRIEVAL_EVAL_CASES
from retriever import load_retrieval_texts, retrieve_best_section


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate section-level retrieval across the content corpus."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a non-zero status code if any expected retrieval case fails.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    content_texts = load_retrieval_texts()
    failures = []

    print("Section retrieval evaluation")
    print("=" * 72)
    print("Dataset: representative test cases derived from current content and retrieval")

    for case in RETRIEVAL_EVAL_CASES:
        question = case["question"]
        expected_article = case["expected_article"]
        expected_heading = case["expected_heading"]
        acceptable_headings = case.get("acceptable_headings", [expected_heading])
        result = retrieve_best_section(question, content_texts=content_texts)

        actual_article = result.article_id if result else None
        actual_heading = result.section_heading if result else None
        passed = actual_article == expected_article and actual_heading in acceptable_headings

        if not passed:
            failures.append(
                {
                    "question": question,
                    "expected_article": expected_article,
                    "expected_heading": expected_heading,
                    "acceptable_headings": acceptable_headings,
                    "actual_article": actual_article,
                    "actual_heading": actual_heading,
                    "score": result.score if result else None,
                }
            )

    print(f"Total cases: {len(RETRIEVAL_EVAL_CASES)}")
    print(f"Passed:      {len(RETRIEVAL_EVAL_CASES) - len(failures)}")
    print(f"Failed:      {len(failures)}")

    if failures:
        print("\nFailed cases:")
        for failure in failures:
            print(f"- {failure['question']!r}")
            print(f"  expected article: {failure['expected_article']}")
            print(f"  expected heading: {failure['expected_heading']}")
            print(f"  acceptable:       {failure['acceptable_headings']}")
            print(f"  actual article:   {failure['actual_article']}")
            print(f"  actual heading:   {failure['actual_heading']}")
            print(f"  score:            {failure['score']}")

    if args.strict and failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
