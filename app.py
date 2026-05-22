import json
import logging
import hmac
import secrets
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import (
    ALLOW_DEV_LOGIN,
    TEMP_LOGIN_PASSWORD,
    TEMP_LOGIN_USERNAME,
    authenticate_with_ldap,
)
from config import (
    DEFAULT_FLASK_SECRET,
    LOGIN_RATE_LIMIT_ATTEMPTS_DEFAULT,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS_DEFAULT,
    build_realtime_session_payload,
    configure_session_security,
    current_openai_api_key,
    current_runtime_mode,
    env_flag,
    env_flag_with_optional,
    env_int,
    env_list,
    flask_secret_key,
    internal_kb_allowed_users,
    internal_kb_default_enabled,
    internal_kb_enabled,
    login_rate_limit_attempts,
    login_rate_limit_window_seconds,
    realtime_support_enabled,
    validate_startup_config,
)
from logging_store import init_logging_db, log_feedback, log_request
from input_guard import classify_input_guard
from query_classifier import classify_query_with_openai
from realtime_tools import dispatch_realtime_tool_call
from response_builder import (
    build_additional_troubleshooting_steps,
    build_guided_context,
    build_no_steps_message,
    build_quick_summary,
    build_response_blocks,
    build_escalation_summary_text,
    build_contact_support_items,
    build_support_topic_title,
    build_ticket_help_items,
    build_tone_profile,
    classify_response_profile,
    detect_disambiguation_options,
    extract_step_items,
    extract_common_symptoms,
    format_source_name,
    should_show_context,
)
from support_service import resolve_question


CSRF_SESSION_KEY = "_csrf_token"
FORM_POST_ENDPOINTS = {"login", "index"}
FAILED_LOGIN_ATTEMPTS = {}
LOGGER = logging.getLogger(__name__)


def remove_repeated_escalation_contact(escalation_text, guided_steps):
    if not escalation_text or not guided_steps:
        return escalation_text

    joined_steps = " ".join(guided_steps).lower()
    if "contact the cca it helpdesk" not in joined_steps and "contact cca it" not in joined_steps:
        return escalation_text

    kept_lines = []
    for line in escalation_text.splitlines():
        lowered = line.lower()
        repeats_contact_path = (
            "contact the cca it helpdesk" in lowered
            or "contact cca it" in lowered
            or "contact cca it support" in lowered
        )
        if repeats_contact_path:
            continue
        kept_lines.append(line)

    return "\n".join(kept_lines).strip() or None


def csrf_token_for_session(session_data):
    """
    Return a stable CSRF token for a Flask session-like mapping.
    """
    token = session_data.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session_data[CSRF_SESSION_KEY] = token
    return token


def csrf_token():
    return csrf_token_for_session(session)


def valid_csrf_token(submitted_token):
    expected_token = session.get(CSRF_SESSION_KEY)
    if not expected_token or not submitted_token:
        return False
    return hmac.compare_digest(str(expected_token), str(submitted_token))


def csrf_failure_response():
    return "The form session expired. Please reload the page and try again.", 400


def current_monotonic_time():
    return time.monotonic()


def login_rate_limit_key():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    first_forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    return first_forwarded_ip or request.remote_addr or "unknown"


def get_login_failure_state(key, now=None):
    now = current_monotonic_time() if now is None else now
    state = FAILED_LOGIN_ATTEMPTS.get(key)
    if not state:
        return None
    if now - state["first_failed_at"] > login_rate_limit_window_seconds():
        FAILED_LOGIN_ATTEMPTS.pop(key, None)
        return None
    return state


def login_rate_limited(key=None):
    if login_rate_limit_attempts() <= 0:
        return False
    key = key or login_rate_limit_key()
    state = get_login_failure_state(key)
    return bool(state and state["count"] >= login_rate_limit_attempts())


def register_failed_login(key=None):
    if login_rate_limit_attempts() <= 0:
        return
    key = key or login_rate_limit_key()
    now = current_monotonic_time()
    state = get_login_failure_state(key, now=now)
    if not state:
        state = {"count": 0, "first_failed_at": now}
        FAILED_LOGIN_ATTEMPTS[key] = state
    state["count"] += 1


def clear_failed_login(key=None):
    key = key or login_rate_limit_key()
    FAILED_LOGIN_ATTEMPTS.pop(key, None)


def internal_kb_user_authorized():
    if not internal_kb_enabled():
        return False

    username = str(session.get("username") or "").strip().lower()
    if not username:
        return False

    return username in internal_kb_allowed_users()


def internal_kb_mode_requested():
    if not internal_kb_user_authorized():
        return False
    if internal_kb_default_enabled():
        return True
    return request.form.get("internal_mode") == "1" or request.args.get("internal_mode") == "1"


def record_log_failure(operation, exc):
    """
    Record logging failures without echoing user-provided text.
    """
    LOGGER.error(
        "Support logging failed during %s. exception_type=%s",
        operation,
        exc.__class__.__name__,
    )


def safe_log_request(**kwargs):
    try:
        return log_request(**kwargs)
    except Exception as exc:
        record_log_failure("request logging", exc)
        return None


def safe_log_feedback(**kwargs):
    try:
        log_feedback(**kwargs)
        return True
    except Exception as exc:
        record_log_failure("feedback logging", exc)
        return False


validate_startup_config()

app = Flask(__name__)
app.secret_key = flask_secret_key()
configure_session_security(app)
app.jinja_env.globals["csrf_token"] = csrf_token

init_logging_db()


@app.before_request
def require_csrf_for_form_posts():
    if request.method != "POST":
        return None
    if request.endpoint not in FORM_POST_ENDPOINTS:
        return None
    if valid_csrf_token(request.form.get("csrf_token")):
        return None
    return csrf_failure_response()

def require_logged_in():
    if not session.get("logged_in"):
        return False
    return True


def create_realtime_client_secret():
    api_key = current_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    payload = json.dumps(build_realtime_session_payload()).encode("utf-8")
    openai_request = urllib_request.Request(
        "https://api.openai.com/v1/realtime/client_secrets",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib_request.urlopen(openai_request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    error_message = None
    if request.method == "POST":
        rate_limit_key = login_rate_limit_key()
        if login_rate_limited(rate_limit_key):
            return render_template(
                "login.html",
                error_message="Too many unsuccessful sign-in attempts. Wait a few minutes and try again.",
                allow_dev_login=ALLOW_DEV_LOGIN,
            ), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        authenticated, error_message = authenticate_with_ldap(username, password)

        if not authenticated and ALLOW_DEV_LOGIN:
            if username == TEMP_LOGIN_USERNAME and password == TEMP_LOGIN_PASSWORD:
                authenticated = True
                error_message = None

        if authenticated:
            clear_failed_login(rate_limit_key)
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))
        register_failed_login(rate_limit_key)
        if login_rate_limited(rate_limit_key):
            return render_template(
                "login.html",
                error_message="Too many unsuccessful sign-in attempts. Wait a few minutes and try again.",
                allow_dev_login=ALLOW_DEV_LOGIN,
            ), 429

    return render_template(
        "login.html",
        error_message=error_message,
        allow_dev_login=ALLOW_DEV_LOGIN,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/realtime", methods=["GET"])
def realtime_console():
    if not require_logged_in():
        return redirect(url_for("login"))
    if not realtime_support_enabled():
        return "Realtime support is not available in this environment.", 503

    return render_template("realtime.html")


@app.route("/realtime/session", methods=["POST"])
def realtime_session():
    if not require_logged_in():
        return jsonify({"error": "Authentication required."}), 401
    if not realtime_support_enabled():
        return jsonify({"error": "Realtime support is not available in this environment."}), 503

    try:
        session_response = create_realtime_client_secret()
        client_secret = (
            ((session_response.get("client_secret") or {}).get("value"))
            or session_response.get("value")
            or ""
        ).strip()
        if not client_secret:
            return jsonify({"error": "Realtime session token was not returned."}), 502

        session_info = session_response.get("session") or {}
        prompt_info = session_info.get("prompt") or {}
        return jsonify(
            {
                "client_secret": client_secret,
                "expires_at": session_response.get("expires_at"),
                "session": {
                    "id": session_info.get("id"),
                    "model": session_info.get("model"),
                    "voice": ((session_info.get("audio") or {}).get("output") or {}).get("voice"),
                    "prompt_id": prompt_info.get("id"),
                },
            }
        )
    except urllib_error.HTTPError as exc:
        try:
            error_body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            error_body = {}
        message = (
            (((error_body.get("error") or {}).get("message")) if isinstance(error_body, dict) else None)
            or "Failed to create a Realtime client secret."
        )
        return jsonify({"error": message}), 502
    except Exception:
        return jsonify({"error": "Failed to create a Realtime client secret."}), 500


@app.route("/realtime/tool", methods=["POST"])
def realtime_tool():
    if not require_logged_in():
        return jsonify({"error": "Authentication required."}), 401
    if not realtime_support_enabled():
        return jsonify({"error": "Realtime support is not available in this environment."}), 503

    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    arguments = payload.get("arguments", {})
    call_id = payload.get("call_id")

    if not name:
        return jsonify({"error": "Tool name is required."}), 400

    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return jsonify({"error": "Tool arguments must be valid JSON."}), 400

    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return jsonify({"error": "Tool arguments must be a JSON object."}), 400

    try:
        result = dispatch_realtime_tool_call(name, arguments)
        return jsonify(
            {
                "ok": True,
                "name": name,
                "call_id": call_id,
                "result": result,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except TypeError as exc:
        return jsonify({"error": f"Invalid arguments for {name}: {exc}"}), 400
    except Exception:
        return jsonify({"error": "Tool execution failed."}), 500


@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    rendered_response = None
    full_document_text = None
    show_response = False
    show_password_reset_portal = False
    password_reset_portal_url = None
    escalation_text = None
    source_name = None
    section_heading = None
    retrieval_confidence = None
    supported = False
    response_type = None
    request_log_id = None
    feedback_submitted = False
    llm_used = False
    asked_question = None
    disambiguation_options = []
    guided_context = None
    guided_steps = []
    common_symptoms = []
    additional_steps = []
    quick_summary = None
    support_title = None
    missing_steps_message = None
    ticket_help_items = []
    response_profile = {
        "kind": "troubleshooting",
        "primary_label": "Try this first",
        "show_followup": True,
        "show_feedback": True,
        "escalation_title": "Need help from IT?",
    }
    followup_status = None
    tone_profile = build_tone_profile()
    query_analysis = None
    agent_triage = None
    suggested_missing_info = []
    ticket_summary = None
    confidence_note = None
    input_guard_response = None
    retrieval_question = None
    internal_mode = internal_kb_mode_requested()
    internal_notes = None

    if request.method == "POST":
        form_type = request.form.get("form_type", "question")

        if form_type == "feedback":
            show_response = True
            feedback_submitted = True
            rendered_response = "Your response has been recorded."

            try:
                request_log_id_raw = request.form.get("request_log_id", "").strip()
                request_log_id = int(request_log_id_raw) if request_log_id_raw else None
                helpful = request.form.get("helpful", "0") == "1"
                safe_log_feedback(request_log_id=request_log_id, helpful=helpful)
            except Exception as exc:
                record_log_failure("feedback form handling", exc)
        else:
            show_response = True
            question = request.form.get("question", "")
            asked_question = question
            original_request_log_id_raw = request.form.get("request_log_id", "").strip()
            original_request_log_id = (
                int(original_request_log_id_raw) if original_request_log_id_raw else None
            )
            guard_result = classify_input_guard(question)
            if guard_result and not guard_result.should_retrieve:
                input_guard_response = guard_result
                response_type = f"input_guard_{guard_result.kind}"
                rendered_response = guard_result.summary
                disambiguation_options = []
            else:
                if guard_result and guard_result.route_to_contact:
                    query_analysis = {"intent": "contact", "topic": "general", "confidence": 1.0}
                    preferred_article_ids = ["contact-it.txt"]
                    retrieval_question = "helpdesk phone"
                else:
                    query_analysis = classify_query_with_openai(question)
                    preferred_article_ids = None
                    retrieval_question = question
                disambiguation_options = detect_disambiguation_options(
                    question,
                    query_analysis=query_analysis,
                )

            try:
                if input_guard_response:
                    pass
                elif disambiguation_options:
                    response_type = "disambiguation"
                    rendered_response = (
                        "This issue could map to more than one procedure. Choose the system you need help with."
                    )
                else:
                    result = resolve_question(
                        retrieval_question or question,
                        query_analysis=query_analysis,
                        preferred_article_ids=preferred_article_ids,
                        include_internal=internal_mode,
                    )
                    source_name = result["source_name"]
                    section_heading = result["section_heading"]
                    retrieval_confidence = result["retrieval_confidence"]
                    full_document_text = result["full_document_text"]
                    rendered_response = result["rendered_response"]
                    supported = result["supported"]
                    response_type = result["response_type"]
                    escalation_text = result["escalation_text"]
                    response_profile = classify_response_profile(
                        question=question,
                        source_name=source_name,
                        section_heading=section_heading,
                        content_text=full_document_text,
                    )
                    escalation_text = build_escalation_summary_text(
                        escalation_text,
                        response_profile=response_profile,
                    )
                    show_password_reset_portal = result["show_password_reset_portal"]
                    password_reset_portal_url = result["password_reset_portal_url"]
                    llm_used = result["llm_used"]
                    agent_triage = result.get("agent_triage")
                    suggested_missing_info = result.get("suggested_missing_info") or []
                    ticket_summary = result.get("ticket_summary")
                    confidence_note = result.get("confidence_note")
                    internal_notes = result.get("internal_notes")

                    if form_type == "followup":
                        followup_status = request.form.get("resolution", "").strip().lower()
                        request_log_id = original_request_log_id
                        if followup_status in {"yes", "no"} and original_request_log_id:
                            try:
                                feedback_submitted = safe_log_feedback(
                                    request_log_id=original_request_log_id,
                                    helpful=(followup_status == "yes"),
                                )
                            except Exception as exc:
                                record_log_failure("follow-up feedback handling", exc)
                        if followup_status == "no":
                            additional_steps = build_additional_troubleshooting_steps(
                                question=question,
                                source_name=source_name,
                                content_text=full_document_text,
                            )
                            if not escalation_text:
                                escalation_text = (
                                    "Contact CCA IT Support if the documented steps and additional troubleshooting do not resolve the issue."
                                )
                            escalation_text = build_escalation_summary_text(
                                escalation_text,
                                response_profile=response_profile,
                            )

            except Exception:
                supported = bool(source_name)
                response_type = "documentation_unavailable"
                rendered_response = "The official documentation for this topic is currently unavailable."

            if form_type != "followup":
                try:
                    request_log_id = safe_log_request(
                        question=question,
                        routed_topic=source_name,
                        article_id=source_name,
                        supported=supported,
                        escalation_flag=bool(escalation_text),
                        response_type=response_type or "documentation_unavailable",
                        llm_used=llm_used,
                    )
                except Exception as exc:
                    record_log_failure("request log handling", exc)
            elif request_log_id is None:
                request_log_id = original_request_log_id

            if not input_guard_response and not disambiguation_options and rendered_response:
                tone_profile = build_tone_profile(question=question, source_name=source_name)
                support_title = build_support_topic_title(
                    question=question,
                    source_name=source_name,
                    section_heading=section_heading,
                    content_text=full_document_text,
                )
                quick_summary = build_quick_summary(
                    question=question,
                    source_name=source_name,
                    section_heading=section_heading,
                    content_text=full_document_text,
                    answer_text=rendered_response,
                )
                guided_context = build_guided_context(
                    question=question,
                    section_heading=section_heading,
                    source_name=source_name,
                    content_text=full_document_text,
                )
                guided_steps = extract_step_items(
                    rendered_response,
                    content_text=full_document_text,
                    question=question,
                    section_heading=section_heading,
                )
                if quick_summary and guided_steps and guided_steps[0].strip() == quick_summary.strip():
                    if len(guided_steps) == 1:
                        quick_summary = None
                    else:
                        guided_steps = guided_steps[1:]
                if response_profile.get("kind") == "contact":
                    contact_items = build_contact_support_items(full_document_text)
                    if contact_items:
                        guided_steps = contact_items
                escalation_text = remove_repeated_escalation_contact(escalation_text, guided_steps)
                common_symptoms = extract_common_symptoms(
                    rendered_response,
                    content_text=full_document_text,
                    question=question,
                    section_heading=section_heading,
                )
                if followup_status == "no" and response_profile.get("show_followup", True):
                    additional_steps = build_additional_troubleshooting_steps(
                        question=question,
                        source_name=source_name,
                        content_text=full_document_text,
                    )
                else:
                    additional_steps = []
                if not guided_steps:
                    missing_steps_message = build_no_steps_message()
                ticket_help_items = build_ticket_help_items(
                    question=question,
                    source_name=source_name,
                    content_text=full_document_text,
                    response_profile=response_profile,
                )

    return render_template(
        "index.html",
        answer_blocks=build_response_blocks(rendered_response),
        build_response_blocks=build_response_blocks,
        additional_steps=additional_steps,
        asked_question=asked_question,
        disambiguation_options=disambiguation_options,
        followup_status=followup_status,
        guided_context=guided_context,
        quick_summary=quick_summary,
        common_symptoms=common_symptoms,
        show_context=should_show_context(
            guided_context,
            question=asked_question,
            section_heading=section_heading,
        ),
        guided_steps=guided_steps,
        rendered_response=rendered_response,
        full_document_text=full_document_text,
        display_source_name=format_source_name(source_name),
        missing_steps_message=missing_steps_message,
        show_response=show_response,
        show_password_reset_portal=show_password_reset_portal,
        password_reset_portal_url=password_reset_portal_url,
        escalation_text=escalation_text,
        source_name=source_name,
        support_title=support_title,
        ticket_help_items=ticket_help_items,
        response_profile=response_profile,
        tone_profile=tone_profile,
        section_heading=section_heading,
        retrieval_confidence=retrieval_confidence,
        request_log_id=request_log_id,
        feedback_submitted=feedback_submitted,
        agent_triage=agent_triage,
        suggested_missing_info=suggested_missing_info,
        ticket_summary=ticket_summary,
        confidence_note=confidence_note,
        input_guard_response=input_guard_response,
        response_type=response_type,
        internal_mode=internal_mode,
        internal_notes=internal_notes,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
