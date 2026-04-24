from flask import Flask, request, render_template_string
from pathlib import Path
from datetime import datetime, UTC
import re
import sqlite3

from retriever import load_retrieval_texts, retrieve_best_section
from router import load_content_texts, select_response

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "it_help_logs.db"


def init_logging_db():
    """
    Initialize the SQLite logging database.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                raw_question TEXT NOT NULL,
                routed_topic TEXT,
                article_id TEXT,
                supported INTEGER NOT NULL,
                escalation_flag INTEGER NOT NULL,
                response_type TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                request_log_id INTEGER,
                helpful INTEGER NOT NULL,
                comment TEXT,
                FOREIGN KEY (request_log_id) REFERENCES request_logs(id)
            )
            """
        )
        conn.commit()


def log_request(question, routed_topic, supported, escalation_flag, response_type, article_id=None):
    """
    Insert one request log record.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO request_logs (
                created_at,
                raw_question,
                routed_topic,
                article_id,
                supported,
                escalation_flag,
                response_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                question,
                routed_topic,
                article_id,
                int(supported),
                int(escalation_flag),
                response_type,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def log_feedback(request_log_id, helpful, comment=None):
    """
    Insert one feedback log record.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO feedback_logs (
                created_at,
                request_log_id,
                helpful,
                comment
            ) VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                request_log_id,
                int(helpful),
                comment,
            ),
        )
        conn.commit()


def extract_first_url(content_text):
    """
    Return the first URL found in documentation text, if any.
    """
    if not content_text:
        return None

    match = re.search(r"https?://[^\s<>\"]+", content_text)
    if not match:
        return None

    return match.group(0).rstrip(".,);")


def extract_escalation_text(content_text):
    """
    Return explicit escalation lines from documentation, if any.
    """
    if not content_text:
        return None

    escalation_lines = []
    for line in content_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            continue
        if (
            "contact it" in lowered
            or "contact the it help desk" in lowered
            or "contact the it helpdesk" in lowered
            or "please contact it support" in lowered
        ):
            escalation_lines.append(stripped)

    if not escalation_lines:
        return None

    return "\n".join(escalation_lines)


def format_source_name(source_name):
    """
    Convert internal article filenames into user-friendly titles.
    """
    if not source_name:
        return None

    cleaned_name = source_name.removesuffix(".txt").replace("-", " ").replace("_", " ").strip()
    if not cleaned_name:
        return None

    return cleaned_name.title()


HTML = """
<!doctype html>
<html>
  <head>
    <title>IT Help Assistant</title>
    <style>
      body {
        font-family: "Myriad Pro", Arial, sans-serif;
        background: #F5F6F7;
        color: #231F20;
        margin: 0;
        padding: 0;
      }

      .page {
        max-width: 960px;
        margin: 0 auto;
        padding: 40px 24px 56px;
      }

      h1 {
        color: #9A111F;
        margin: 0 0 6px;
      }

      .subtitle {
        color: #66686A;
        font-size: 15px;
        margin: 0 0 28px;
      }

      .card {
        background: #ffffff;
        border: 1px solid #D1D2D4;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
      }

      h2 {
        color: #9A111F;
        margin: 0 0 10px;
      }

      ul.examples {
        color: #66686A;
        font-size: 14px;
        margin: 8px 0 20px;
        padding-left: 18px;
      }

      ul.examples li {
        margin-bottom: 6px;
      }

      textarea {
        width: 100%;
        min-height: 110px;
        padding: 12px;
        font-size: 15px;
        line-height: 1.5;
        font-family: inherit;
        border: 1px solid #D1D2D4;
        background: #F9F9F9;
        box-sizing: border-box;
        resize: vertical;
      }

      textarea:focus {
        outline: none;
        border-color: #9A111F;
        background: #ffffff;
      }

      button {
        margin-top: 14px;
        background: #9A111F;
        color: #ffffff;
        border: none;
        padding: 10px 22px;
        font-size: 15px;
        font-weight: 500;
        cursor: pointer;
      }

      button:hover {
        opacity: 0.95;
      }

      .response-card {
        margin-top: 32px;
        padding: 28px 32px;
        border: 1px solid #D1D2D4;
        background: #ffffff;
        max-width: 800px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
      }

      .response-title {
        margin: 0 0 18px;
        color: #9A111F;
        font-size: 22px;
        font-weight: 600;
        line-height: 1.25;
      }

      .response-heading {
        margin: 0 0 12px;
        color: #66686A;
        font-size: 14px;
        font-weight: 600;
        text-transform: none;
      }

      .response-body {
        font-size: 17px;
        line-height: 1.8;
        color: #231F20;
      }

      .response-body p {
        margin: 0 0 16px 0;
      }

      .response-body p:last-child {
        margin-bottom: 0;
      }

      .response-action {
        margin: 18px 0 0;
        padding-top: 16px;
        border-top: 1px solid #E5E6E8;
        font-weight: 500;
      }

      .response-action a {
        color: #9A111F;
        text-decoration: underline;
        word-break: break-word;
      }

      .response-escalation {
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid #E5E6E8;
        font-size: 14px;
        line-height: 1.6;
        color: #231F20;
      }

      .response-escalation h3 {
        margin: 0 0 8px;
        color: #231F20;
        font-size: 15px;
        font-weight: 600;
      }

      .response-escalation p {
        margin: 0 0 12px;
      }

      .response-escalation .next-step {
        color: #66686A;
      }

      .response-escalation p:last-child {
        margin-bottom: 0;
      }

      .match-details {
        margin-top: 18px;
        padding: 14px 16px;
        border-top: 1px solid #EDEEEF;
        background: #F8F9FA;
      }

      .match-details h3 {
        margin: 0 0 10px;
        color: #231F20;
        font-size: 14px;
        font-weight: 600;
      }

      .match-row {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 6px 12px;
        font-size: 13px;
        line-height: 1.5;
      }

      .match-label {
        color: #66686A;
        font-weight: 600;
      }

      .match-value {
        color: #231F20;
        word-break: break-word;
      }

      .response-source {
        margin-top: 14px;
        font-size: 12px;
        color: #66686A;
      }

      .feedback-section {
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid #E5E6E8;
      }

      .feedback-title {
        margin: 0 0 10px;
        font-size: 14px;
        font-weight: 600;
        color: #231F20;
      }

      .feedback-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .feedback-button {
        margin-top: 0;
        padding: 8px 16px;
        font-size: 14px;
      }

      .feedback-thanks {
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid #E5E6E8;
        font-size: 14px;
        color: #231F20;
      }
    </style>
  </head>
  <body>
    <div class="page">
      <h1>IT Help Assistant</h1>
      <p class="subtitle">
        Answers common IT questions using official Community College of Aurora documentation.
      </p>

      <div class="card">
        <h2>Ask a question</h2>
        <p>Example questions:</p>
        <ul class="examples">
          <li>How do I reset my password?</li>
          <li>How do I access my student email?</li>
          <li>Wi‑Fi isn’t working</li>
          <li>Where do I submit assignments?</li>
        </ul>

        <form method="POST" action="/#response">
          <textarea name="question" placeholder="Type your question here..."></textarea>
          <br>
          <button type="submit">Get help</button>
        </form>
      </div>

      {% if show_response %}
        <div class="response-card" id="response">
          <h2 class="response-title">IT Help Response</h2>

          {% if section_heading %}
            <div class="response-heading">{{ section_heading }}</div>
          {% endif %}

          <div class="response-body">
            {% for paragraph in rendered_response.split('\n\n') %}
              <p>{{ paragraph }}</p>
            {% endfor %}
          </div>

          {% if show_password_reset_portal %}
            <div class="response-action">
              {% if password_reset_portal_url %}
                <a href="{{ password_reset_portal_url }}" target="_blank" rel="noopener noreferrer">
                  Open the Password Reset Portal
                </a>
              {% else %}
                Password Reset Portal
              {% endif %}
            </div>
          {% endif %}

          {% if escalation_text %}
            <div class="response-escalation">
              <h3>Still need help?</h3>
              <p class="next-step">If the steps above do not solve the issue, use this next step:</p>
              {% for paragraph in escalation_text.split('\n') %}
                <p>{{ paragraph }}</p>
              {% endfor %}
            </div>
          {% endif %}

          {% if source_name or section_heading or retrieval_confidence %}
            <div class="match-details">
              <h3>Source information</h3>
              <div class="match-row">
                <div class="match-label">Source article</div>
                <div class="match-value">{{ display_source_name or "Not available" }}</div>
                <div class="match-label">Matched section</div>
                <div class="match-value">{{ section_heading or "Not available" }}</div>
                <div class="match-label">Confidence</div>
                <div class="match-value">{{ retrieval_confidence or "Not available" }}</div>
              </div>
            </div>
          {% endif %}

          <div class="response-source">
            Based on official CCA IT documentation.
          </div>

          {% if request_log_id and not feedback_submitted %}
            <div class="feedback-section">
              <div class="feedback-title">Was this helpful?</div>
              <div class="feedback-actions">
                <form method="POST" action="/#response">
                  <input type="hidden" name="form_type" value="feedback">
                  <input type="hidden" name="request_log_id" value="{{ request_log_id }}">
                  <input type="hidden" name="helpful" value="1">
                  <button class="feedback-button" type="submit">Yes, this helped</button>
                </form>
                <form method="POST" action="/#response">
                  <input type="hidden" name="form_type" value="feedback">
                  <input type="hidden" name="request_log_id" value="{{ request_log_id }}">
                  <input type="hidden" name="helpful" value="0">
                  <button class="feedback-button" type="submit">No, I still need help</button>
                </form>
              </div>
            </div>
          {% endif %}

          {% if feedback_submitted %}
            <div class="feedback-thanks">Thank you for the feedback.</div>
          {% endif %}

        </div>

        <script>
          document.getElementById("response")
            .scrollIntoView({ behavior: "auto", block: "start" });
        </script>
      {% endif %}
    </div>
  </body>
</html>
"""

init_logging_db()


@app.route("/", methods=["GET", "POST"])
def index():
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

            try:
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

            except Exception:
                supported = bool(source_name)
                response_type = "documentation_unavailable"
                rendered_response = (
                    "The official documentation for this topic is currently unavailable."
                )

            try:
                request_log_id = log_request(
                    question=question,
                    routed_topic=source_name,
                    article_id=source_name,
                    supported=supported,
                    escalation_flag=bool(escalation_text),
                    response_type=response_type or "documentation_unavailable",
                )
            except Exception:
                pass

    return render_template_string(
        HTML,
        rendered_response=rendered_response,
        full_document_text=full_document_text,
        display_source_name=format_source_name(source_name),
        show_response=show_response,
        show_password_reset_portal=show_password_reset_portal,
        password_reset_portal_url=password_reset_portal_url,
        escalation_text=escalation_text,
        source_name=source_name,
        section_heading=section_heading,
        retrieval_confidence=retrieval_confidence,
        request_log_id=request_log_id,
        feedback_submitted=feedback_submitted,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
