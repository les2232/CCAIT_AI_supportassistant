#!/usr/bin/env python3
import json
import os
import sys
from contextlib import contextmanager

from agent_service import maybe_run_agent_triage


BASE_RESULT = {
    "source_name": "wifi-troubleshooting.txt",
    "section_heading": "First-time setup:",
    "retrieval_confidence": "high",
    "full_document_text": "CCA-Students is an open network and does not require a password.",
    "rendered_response": "Open Wi-Fi settings and choose CCA-Students.",
    "supported": True,
    "response_type": "documentation_article",
    "escalation_text": "Contact the CCA IT Helpdesk if you cannot connect to CCA-Students.",
    "show_password_reset_portal": False,
    "password_reset_portal_url": None,
    "llm_used": False,
}


@contextmanager
def patched_env(**values):
    original = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class FakeRunResult:
    def __init__(self, final_output):
        self.final_output = final_output


class FakeRunner:
    last_input = None

    @classmethod
    def run_sync(cls, agent, agent_input):
        cls.last_input = agent_input
        return FakeRunResult(
            json.dumps(
                {
                    "triage_note": "The KB has enough Wi-Fi setup context for initial triage.",
                    "suggested_missing_info": ["Device type", "Campus location"],
                    "ticket_summary": "Student cannot connect to CCA-Students after trying setup steps.",
                    "confidence_note": "Grounded in wifi-troubleshooting.txt.",
                    "escalation_required": False,
                }
            )
        )


class FailingRunner:
    @classmethod
    def run_sync(cls, agent, agent_input):
        raise RuntimeError("agent failed")


def fake_agent_factory():
    return object()


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_feature_flag_off_returns_original():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="0", OPENAI_API_KEY="test-key"):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FakeRunner,
            agent_factory=fake_agent_factory,
        )
    assert_true(actual is result, "feature flag off should return the original result object")


def test_missing_key_returns_original():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="1", OPENAI_API_KEY=None):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FakeRunner,
            agent_factory=fake_agent_factory,
        )
    assert_true(actual is result, "missing OPENAI_API_KEY should return the original result object")


def test_agent_failure_returns_original():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="1", OPENAI_API_KEY="test-key"):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FailingRunner,
            agent_factory=fake_agent_factory,
        )
    assert_true(actual is result, "agent failure should return the original result object")


def test_fake_agent_adds_ticket_summary_and_context():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="1", OPENAI_API_KEY="test-key"):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FakeRunner,
            agent_factory=fake_agent_factory,
        )

    assert_true(actual is not result, "successful agent run should return an enriched copy")
    assert_true(actual["ticket_summary"], "ticket summary should be added")
    assert_true("agent_triage" in actual, "agent triage metadata should be added")

    agent_input = json.loads(FakeRunner.last_input)
    retrieved_context = agent_input["retrieved_kb_context"]
    assert_true(
        retrieved_context["source_name"] == BASE_RESULT["source_name"],
        "retrieved KB source should be passed to the agent",
    )
    assert_true(
        retrieved_context["section_heading"] == BASE_RESULT["section_heading"],
        "retrieved KB section should be passed to the agent",
    )


def test_agent_cannot_suppress_escalation():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="1", OPENAI_API_KEY="test-key"):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FakeRunner,
            agent_factory=fake_agent_factory,
        )
    assert_true(
        actual["agent_triage"]["escalation_required"] is True,
        "existing KB escalation text must force escalation_required metadata",
    )
    assert_true(
        actual["escalation_text"] == BASE_RESULT["escalation_text"],
        "agent metadata must not replace escalation text",
    )


def test_agent_metadata_does_not_replace_kb_fields():
    result = dict(BASE_RESULT)
    with patched_env(ENABLE_AGENTS="1", OPENAI_API_KEY="test-key"):
        actual = maybe_run_agent_triage(
            "How do I connect to Wi-Fi?",
            result,
            runner=FakeRunner,
            agent_factory=fake_agent_factory,
        )

    protected_fields = (
        "source_name",
        "section_heading",
        "rendered_response",
        "supported",
        "response_type",
        "show_password_reset_portal",
        "password_reset_portal_url",
    )
    for field in protected_fields:
        assert_true(
            actual[field] == BASE_RESULT[field],
            f"agent metadata must not replace {field}",
        )


def main():
    tests = [
        test_feature_flag_off_returns_original,
        test_missing_key_returns_original,
        test_agent_failure_returns_original,
        test_fake_agent_adds_ticket_summary_and_context,
        test_agent_cannot_suppress_escalation,
        test_agent_metadata_does_not_replace_kb_fields,
    ]

    failures = []
    print("Agent service evaluation")
    print("=" * 72)
    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failures.append((test.__name__, str(exc)))
            print(f"[FAIL] {test.__name__}: {exc}")

    print()
    print(f"Total cases: {len(tests)}")
    print(f"Passed:      {len(tests) - len(failures)}")
    print(f"Failed:      {len(failures)}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
