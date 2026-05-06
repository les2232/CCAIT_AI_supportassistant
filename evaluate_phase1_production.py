#!/usr/bin/env python3
import io
import logging
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path

from flask import Flask

import app as app_module
import logging_store


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


@contextmanager
def patched_attr(module, name, value):
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, original)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_configurable_logging_db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "nested" / "it_help_logs.db"
        with patched_env(IT_SUPPORT_LOG_DB_PATH=str(db_path)):
            logging_store.init_logging_db()
            request_id = logging_store.log_request(
                question="My password is SuperSecret123 and email me@example.edu",
                routed_topic="password-reset.txt",
                article_id="password-reset.txt",
                supported=True,
                escalation_flag=False,
                response_type="documentation_article",
                llm_used=False,
            )

        assert_true(db_path.exists(), "configured logging database was not created")
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT raw_question FROM request_logs WHERE id = ?",
                (request_id,),
            ).fetchone()

        assert_true(row is not None, "request log row was not written")
        assert_true("SuperSecret123" not in row[0], "password was written to log")
        assert_true("me@example.edu" not in row[0], "email was written to log")
        assert_true("[redacted-password]" in row[0], "redacted password marker missing")
        assert_true("[redacted-email]" in row[0], "redacted email marker missing")


def test_logging_failure_is_recorded_without_user_text():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.ERROR)
    app_module.LOGGER.addHandler(handler)
    previous_level = app_module.LOGGER.level
    app_module.LOGGER.setLevel(logging.ERROR)

    def failing_log_request(**_kwargs):
        raise RuntimeError("database unavailable for DontLogThis123")

    try:
        with patched_attr(app_module, "log_request", failing_log_request):
            result = app_module.safe_log_request(
                question="My password is DontLogThis123",
                routed_topic="password-reset.txt",
                article_id="password-reset.txt",
                supported=True,
                escalation_flag=False,
                response_type="documentation_article",
                llm_used=False,
            )
    finally:
        app_module.LOGGER.removeHandler(handler)
        app_module.LOGGER.setLevel(previous_level)

    log_output = stream.getvalue()
    assert_true(result is None, "safe_log_request should return None on write failure")
    assert_true("Support logging failed during request logging" in log_output, "failure was not logged")
    assert_true("RuntimeError" in log_output, "failure log should include the exception type")
    assert_true("DontLogThis123" not in log_output, "user input leaked into logging failure")


def logged_in_client():
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "phase1-test"
    return client


def test_realtime_disabled_behavior():
    with patched_env(ENABLE_REALTIME_SUPPORT="0"):
        client = logged_in_client()
        response = client.get("/realtime")
        assert_true(response.status_code == 503, "/realtime should be unavailable when disabled")
        assert_true(
            "Realtime support is not available" in response.get_data(as_text=True),
            "disabled realtime page did not return safe message",
        )

        session_response = client.post("/realtime/session")
        assert_true(session_response.status_code == 503, "/realtime/session should be unavailable when disabled")
        assert_true(
            session_response.get_json()["error"] == "Realtime support is not available in this environment.",
            "disabled realtime session returned unexpected payload",
        )

        tool_response = client.post("/realtime/tool", json={"name": "search_support_kb", "arguments": {}})
        assert_true(tool_response.status_code == 503, "/realtime/tool should be unavailable when disabled")


def test_realtime_enabled_behavior():
    fake_response = {
        "client_secret": {"value": "test-client-secret"},
        "expires_at": 1234567890,
        "session": {
            "id": "sess_test",
            "model": "gpt-realtime",
            "audio": {"output": {"voice": "marin"}},
            "prompt": {"id": "prompt_test"},
        },
    }

    with patched_env(ENABLE_REALTIME_SUPPORT="1"):
        client = logged_in_client()
        page_response = client.get("/realtime")
        assert_true(page_response.status_code == 200, "/realtime should render when enabled")

        with patched_attr(app_module, "create_realtime_client_secret", lambda: fake_response):
            session_response = client.post("/realtime/session")

        assert_true(session_response.status_code == 200, "/realtime/session should work when enabled")
        payload = session_response.get_json()
        assert_true(payload["client_secret"] == "test-client-secret", "client secret payload was not returned")
        assert_true(payload["session"]["id"] == "sess_test", "session metadata was not returned")


def test_session_cookie_config_defaults():
    with patched_env(APP_ENV=None, SESSION_COOKIE_SECURE=None, SESSION_COOKIE_SAMESITE=None):
        flask_app = Flask("phase1-dev-cookie-test")
        app_module.configure_session_security(flask_app)
        assert_true(flask_app.config["SESSION_COOKIE_HTTPONLY"] is True, "HTTP-only cookie default missing")
        assert_true(flask_app.config["SESSION_COOKIE_SAMESITE"] == "Lax", "SameSite default should be Lax")
        assert_true(flask_app.config["SESSION_COOKIE_SECURE"] is False, "local dev should allow non-secure cookies")

    with patched_env(APP_ENV="production", SESSION_COOKIE_SECURE=None, SESSION_COOKIE_SAMESITE=None):
        flask_app = Flask("phase1-prod-cookie-test")
        app_module.configure_session_security(flask_app)
        assert_true(flask_app.config["SESSION_COOKIE_SECURE"] is True, "production should default to secure cookies")

    with patched_env(APP_ENV="production", SESSION_COOKIE_SECURE="", SESSION_COOKIE_SAMESITE=""):
        flask_app = Flask("phase1-prod-cookie-blank-test")
        app_module.configure_session_security(flask_app)
        assert_true(flask_app.config["SESSION_COOKIE_SECURE"] is True, "blank secure cookie env should use production default")
        assert_true(flask_app.config["SESSION_COOKIE_SAMESITE"] == "Lax", "blank SameSite env should use Lax default")

    with patched_env(APP_ENV="production", SESSION_COOKIE_SECURE="0", SESSION_COOKIE_SAMESITE="Strict"):
        flask_app = Flask("phase1-cookie-override-test")
        app_module.configure_session_security(flask_app)
        assert_true(flask_app.config["SESSION_COOKIE_SECURE"] is False, "secure cookie env override failed")
        assert_true(flask_app.config["SESSION_COOKIE_SAMESITE"] == "Strict", "SameSite env override failed")


def main():
    tests = [
        test_configurable_logging_db_path,
        test_logging_failure_is_recorded_without_user_text,
        test_realtime_disabled_behavior,
        test_realtime_enabled_behavior,
        test_session_cookie_config_defaults,
    ]

    failures = []
    print("Phase 1 production-readiness evaluation")
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
        raise SystemExit(1)


if __name__ == "__main__":
    main()
