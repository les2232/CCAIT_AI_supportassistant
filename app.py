import os

from flask import Flask, redirect, render_template, request, session, url_for

from auth import (
    ALLOW_DEV_LOGIN,
    TEMP_LOGIN_PASSWORD,
    TEMP_LOGIN_USERNAME,
    authenticate_with_ldap,
)
from llm_answer import polish_answer
from logging_store import DB_PATH, init_logging_db, log_feedback, log_request
from response_builder import (
    build_additional_troubleshooting_steps,
    build_guided_context,
    build_response_blocks,
    build_tone_profile,
    detect_disambiguation_options,
    extract_escalation_text,
    extract_step_items,
    extract_first_url,
    format_source_name,
)
from retriever import load_retrieval_texts, retrieve_best_section
from router import load_content_texts, select_response


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "temporary-dev-session-secret-key")

init_logging_db()


def resolve_question(question):
    """
    Run the existing retrieval-first flow and return renderable response details.
    """
    source_name = None
    section_heading = None
    retrieval_confidence = None
    full_document_text = None
    rendered_response = None
    supported = False
    response_type = None
    escalation_text = None
    show_password_reset_portal = False
    password_reset_portal_url = None
    llm_used = False

    retrieval_texts = load_retrieval_texts()
    retrieval_result = retrieve_best_section(question, content_texts=retrieval_texts)

    if retrieval_result is not None:
        source_name = retrieval_result.article_id
        section_heading = retrieval_result.section_heading
        retrieval_confidence = retrieval_result.confidence
        full_document_text = retrieval_result.full_document_text
        rendered_response = retrieval_result.answer_text
        supported = True
        response_type = "documentation_article"
        escalation_text = extract_escalation_text(full_document_text)

        if source_name == "password-reset.txt":
            show_password_reset_portal = True
            password_reset_portal_url = extract_first_url(full_document_text)
    else:
        routed_texts = load_content_texts()
        source_name, raw_content = select_response(question, routed_texts)

        if source_name is None:
            response_type = "unsupported_topic"
            rendered_response = (
                "I don’t have official CCA IT documentation for that topic yet.\n"
                "For assistance with this issue, please contact the IT Help Desk."
            )
        elif not raw_content or not raw_content.strip():
            supported = True
            response_type = "documentation_unavailable"
            rendered_response = "The official documentation for this topic is currently unavailable."
        else:
            fallback_result = retrieve_best_section(
                question,
                content_texts={source_name: raw_content},
                article_ids=[source_name],
                min_score=1,
            )
            supported = True
            response_type = "documentation_article"
            escalation_text = extract_escalation_text(raw_content)
            full_document_text = raw_content

            if fallback_result is not None:
                section_heading = fallback_result.section_heading
                retrieval_confidence = fallback_result.confidence
                rendered_response = fallback_result.answer_text
            else:
                rendered_response = raw_content.strip()

            if source_name == "password-reset.txt":
                show_password_reset_portal = True
                password_reset_portal_url = extract_first_url(raw_content)

    if response_type == "documentation_article" and rendered_response:
        rendered_response, llm_used = polish_answer(
            question=question,
            section_heading=section_heading,
            article_id=source_name,
            answer_text=rendered_response,
        )

    return {
        "source_name": source_name,
        "section_heading": section_heading,
        "retrieval_confidence": retrieval_confidence,
        "full_document_text": full_document_text,
        "rendered_response": rendered_response,
        "supported": supported,
        "response_type": response_type,
        "escalation_text": escalation_text,
        "show_password_reset_portal": show_password_reset_portal,
        "password_reset_portal_url": password_reset_portal_url,
        "llm_used": llm_used,
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    error_message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        authenticated, error_message = authenticate_with_ldap(username, password)

        if not authenticated and ALLOW_DEV_LOGIN:
            if username == TEMP_LOGIN_USERNAME and password == TEMP_LOGIN_PASSWORD:
                authenticated = True
                error_message = None

        if authenticated:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))

    return render_template(
        "login.html",
        error_message=error_message,
        allow_dev_login=ALLOW_DEV_LOGIN,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


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
    additional_steps = []
    followup_status = None
    tone_profile = build_tone_profile()

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
                log_feedback(request_log_id=request_log_id, helpful=helpful)
            except Exception:
                pass
        else:
            show_response = True
            question = request.form.get("question", "")
            asked_question = question
            original_request_log_id_raw = request.form.get("request_log_id", "").strip()
            original_request_log_id = (
                int(original_request_log_id_raw) if original_request_log_id_raw else None
            )
            disambiguation_options = detect_disambiguation_options(question)

            try:
                if disambiguation_options:
                    response_type = "disambiguation"
                    rendered_response = (
                        "This issue could map to more than one procedure. Choose the system you need help with."
                    )
                else:
                    result = resolve_question(question)
                    source_name = result["source_name"]
                    section_heading = result["section_heading"]
                    retrieval_confidence = result["retrieval_confidence"]
                    full_document_text = result["full_document_text"]
                    rendered_response = result["rendered_response"]
                    supported = result["supported"]
                    response_type = result["response_type"]
                    escalation_text = result["escalation_text"]
                    show_password_reset_portal = result["show_password_reset_portal"]
                    password_reset_portal_url = result["password_reset_portal_url"]
                    llm_used = result["llm_used"]

                    if form_type == "followup":
                        followup_status = request.form.get("resolution", "").strip().lower()
                        request_log_id = original_request_log_id
                        if followup_status in {"yes", "no"} and original_request_log_id:
                            try:
                                log_feedback(
                                    request_log_id=original_request_log_id,
                                    helpful=(followup_status == "yes"),
                                )
                                feedback_submitted = True
                            except Exception:
                                pass
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

            except Exception:
                supported = bool(source_name)
                response_type = "documentation_unavailable"
                rendered_response = "The official documentation for this topic is currently unavailable."

            if form_type != "followup":
                try:
                    request_log_id = log_request(
                        question=question,
                        routed_topic=source_name,
                        article_id=source_name,
                        supported=supported,
                        escalation_flag=bool(escalation_text),
                        response_type=response_type or "documentation_unavailable",
                        llm_used=llm_used,
                    )
                except Exception:
                    pass
            elif request_log_id is None:
                request_log_id = original_request_log_id

            if not disambiguation_options and rendered_response:
                tone_profile = build_tone_profile(question=question, source_name=source_name)
                guided_context = build_guided_context(
                    question=question,
                    section_heading=section_heading,
                    source_name=source_name,
                    content_text=full_document_text,
                )
                guided_steps = extract_step_items(rendered_response, content_text=full_document_text)

    return render_template(
        "index.html",
        answer_blocks=build_response_blocks(rendered_response),
        additional_steps=additional_steps,
        asked_question=asked_question,
        disambiguation_options=disambiguation_options,
        followup_status=followup_status,
        guided_context=guided_context,
        guided_steps=guided_steps,
        rendered_response=rendered_response,
        full_document_text=full_document_text,
        display_source_name=format_source_name(source_name),
        show_response=show_response,
        show_password_reset_portal=show_password_reset_portal,
        password_reset_portal_url=password_reset_portal_url,
        escalation_text=escalation_text,
        source_name=source_name,
        tone_profile=tone_profile,
        section_heading=section_heading,
        retrieval_confidence=retrieval_confidence,
        request_log_id=request_log_id,
        feedback_submitted=feedback_submitted,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
