from query_classifier import classify_query_with_openai


TEST_CASES = [
    {
        "query": "wifi says connected but no internet",
        "intent": "troubleshooting",
        "topic": "wifi",
    },
    {
        "query": "wifi page did not pop up",
        "intent": "troubleshooting",
        "topic": "wifi",
    },
    {
        "query": "student email not working",
        "intent": "troubleshooting",
        "topic": "email",
    },
    {
        "query": "do I need Duo for email",
        "intent": "access",
        "topic": "email",
    },
    {
        "query": "I can't access my class",
        "intent": "access",
        "topic": "d2l",
    },
    {
        "query": "Zoom audio is broken",
        "intent": "troubleshooting",
        "topic": "zoom",
    },
    {
        "query": "projector has no signal",
        "intent": "troubleshooting",
        "topic": "classroom",
    },
    {
        "query": "who do I contact for Zoom help",
        "intent": "contact",
        "topic": "zoom",
    },
    {
        "query": "where is OBL located",
        "intent": "contact",
        "topic": "general",
    },
    {
        "query": "what is D2L",
        "intent": "informational",
        "topic": "d2l",
    },
    {
        "query": "nothing is working",
        "intent": "troubleshooting",
        "topic": "general",
    },
]


def main():
    print("Query classifier evaluation")
    print("=" * 72)

    passed = 0
    failed = 0

    for case in TEST_CASES:
        actual = classify_query_with_openai(case["query"])
        ok = actual["intent"] == case["intent"] and actual["topic"] == case["topic"]
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['query']!r}")
        print(f"  expected: intent={case['intent']}, topic={case['topic']}")
        print(
            f"  actual:   intent={actual['intent']}, topic={actual['topic']}, confidence={actual['confidence']}"
        )
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Total cases: {len(TEST_CASES)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
