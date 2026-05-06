#!/usr/bin/env python3
import os
from contextlib import contextmanager

import app as app_module


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


def csrf_for_client(client):
    with client.session_transaction() as sess:
        return app_module.csrf_token_for_session(sess)


def with_csrf(client, data):
    payload = dict(data)
    payload["csrf_token"] = csrf_for_client(client)
    return payload


def logged_in_client():
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "security-test-user"
    return client


def test_missing_and_invalid_csrf_rejected():
    app_module.FAILED_LOGIN_ATTEMPTS.clear()

    with app_module.app.test_client() as client:
        missing_login = client.post(
            "/login",
            data={"username": "user", "password": "secret"},
        )
        assert_true(missing_login.status_code == 400, "login POST without CSRF should be rejected")

        csrf_for_client(client)
        invalid_login = client.post(
            "/login",
            data={"username": "user", "password": "secret", "csrf_token": "bad-token"},
        )
        assert_true(invalid_login.status_code == 400, "login POST with invalid CSRF should be rejected")

    client = logged_in_client()
    missing_query = client.post("/", data={"question": "hi"}, follow_redirects=True)
    assert_true(missing_query.status_code == 400, "query POST without CSRF should be rejected")

    invalid_query = client.post(
        "/",
        data={"question": "hi", "csrf_token": "bad-token"},
        follow_redirects=True,
    )
    assert_true(invalid_query.status_code == 400, "query POST with invalid CSRF should be rejected")


def test_valid_csrf_allows_login_and_forms():
    app_module.FAILED_LOGIN_ATTEMPTS.clear()

    with app_module.app.test_client() as client:
        with patched_attr(app_module, "authenticate_with_ldap", lambda username, password: (True, None)):
            response = client.post(
                "/login",
                data=with_csrf(
                    client,
                    {
                        "username": "authorized.user",
                        "password": "correct-password",
                    },
                ),
            )
        assert_true(response.status_code == 302, "valid CSRF login should redirect after success")
        assert_true(response.headers["Location"].endswith("/"), "successful login should redirect to index")
        with client.session_transaction() as sess:
            assert_true(sess.get("logged_in") is True, "successful login should set logged_in session")

    client = logged_in_client()
    query_response = client.post(
        "/",
        data=with_csrf(client, {"question": "hi"}),
        follow_redirects=True,
    )
    assert_true(query_response.status_code == 200, "valid CSRF query form should be accepted")
    assert_true("How can I help with CCA technology?" in query_response.get_data(as_text=True), "query response did not render")

    with patched_attr(app_module, "safe_log_feedback", lambda **_kwargs: True):
        feedback_response = client.post(
            "/",
            data=with_csrf(
                client,
                {
                    "form_type": "feedback",
                    "request_log_id": "1",
                    "helpful": "1",
                },
            ),
            follow_redirects=True,
        )
    assert_true(feedback_response.status_code == 200, "valid CSRF feedback form should be accepted")
    assert_true("Your response has been recorded." in feedback_response.get_data(as_text=True), "feedback response did not render")

    with patched_attr(app_module, "safe_log_feedback", lambda **_kwargs: True):
        followup_response = client.post(
            "/",
            data=with_csrf(
                client,
                {
                    "form_type": "followup",
                    "request_log_id": "1",
                    "question": "Connect to Wi-Fi",
                    "resolution": "yes",
                },
            ),
            follow_redirects=True,
        )
    assert_true(followup_response.status_code == 200, "valid CSRF follow-up form should be accepted")
    assert_true("marked as helpful" in followup_response.get_data(as_text=True), "follow-up response did not render")


def test_login_rate_limit_failed_attempts():
    app_module.FAILED_LOGIN_ATTEMPTS.clear()
    auth_calls = {"count": 0}

    def failed_auth(_username, _password):
        auth_calls["count"] += 1
        return False, "Sign-in failed. Check your credentials or contact IT if the issue continues."

    with patched_env(LOGIN_RATE_LIMIT_ATTEMPTS="3", LOGIN_RATE_LIMIT_WINDOW_SECONDS="300"):
        with patched_attr(app_module, "authenticate_with_ldap", failed_auth):
            with app_module.app.test_client() as client:
                headers = {"X-Forwarded-For": "198.51.100.10"}
                for index in range(2):
                    response = client.post(
                        "/login",
                        data=with_csrf(
                            client,
                            {
                                "username": f"user{index}",
                                "password": "wrong-password",
                            },
                        ),
                        headers=headers,
                    )
                    assert_true(response.status_code == 200, "failed login before limit should render login page")

                limited_response = client.post(
                    "/login",
                    data=with_csrf(
                        client,
                        {
                            "username": "another.user",
                            "password": "wrong-password",
                        },
                    ),
                    headers=headers,
                )
                assert_true(limited_response.status_code == 429, "third failed login should be rate limited")
                assert_true(
                    "Too many unsuccessful sign-in attempts" in limited_response.get_data(as_text=True),
                    "rate limit response should show a safe generic message",
                )

                blocked_response = client.post(
                    "/login",
                    data=with_csrf(
                        client,
                        {
                            "username": "authorized.user",
                            "password": "maybe-correct",
                        },
                    ),
                    headers=headers,
                )
                assert_true(blocked_response.status_code == 429, "subsequent login should stay rate limited")
                assert_true(auth_calls["count"] == 3, "rate-limited request should not call LDAP/auth backend")


def test_successful_login_not_broken_and_clears_failures():
    app_module.FAILED_LOGIN_ATTEMPTS.clear()
    headers = {"X-Forwarded-For": "203.0.113.20"}

    with patched_env(LOGIN_RATE_LIMIT_ATTEMPTS="3", LOGIN_RATE_LIMIT_WINDOW_SECONDS="300"):
        with app_module.app.test_client() as client:
            with patched_attr(
                app_module,
                "authenticate_with_ldap",
                lambda _username, _password: (False, "Sign-in failed. Check your credentials or contact IT if the issue continues."),
            ):
                for _index in range(2):
                    client.post(
                        "/login",
                        data=with_csrf(client, {"username": "same.user", "password": "wrong-password"}),
                        headers=headers,
                    )

            assert_true(app_module.get_login_failure_state("203.0.113.20") is not None, "failed login state should exist before success")

            with patched_attr(app_module, "authenticate_with_ldap", lambda _username, _password: (True, None)):
                success = client.post(
                    "/login",
                    data=with_csrf(client, {"username": "same.user", "password": "correct-password"}),
                    headers=headers,
                )

            assert_true(success.status_code == 302, "successful login should not be blocked below the limit")
            assert_true(app_module.get_login_failure_state("203.0.113.20") is None, "successful login should clear failed state")


def main():
    tests = [
        test_missing_and_invalid_csrf_rejected,
        test_valid_csrf_allows_login_and_forms,
        test_login_rate_limit_failed_attempts,
        test_successful_login_not_broken_and_clears_failures,
    ]

    failures = []
    print("Security controls evaluation")
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
