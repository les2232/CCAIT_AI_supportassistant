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
    <title>CCA IT Support Assistant</title>
    <style>
      :root {
        --cca-red: #9A111F;
        --cca-red-dark: #7F0F1A;
        --ink: #1F2933;
        --muted: #5F6C7B;
        --line: #D6DCE3;
        --line-soft: #E7EBF0;
        --surface: #FFFFFF;
        --surface-muted: #F7F9FB;
        --page-top: #EEF2F5;
        --page-bottom: #F8FAFB;
      }

      * {
        box-sizing: border-box;
      }

      body {
        font-family: "Myriad Pro", Arial, sans-serif;
        background: linear-gradient(180deg, var(--page-top) 0%, var(--page-bottom) 100%);
        color: var(--ink);
        margin: 0;
        padding: 0;
      }

      .page {
        max-width: 980px;
        margin: 0 auto;
        padding: 32px 20px 56px;
      }

      .hero {
        margin-bottom: 20px;
        padding: 28px 28px 22px;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: linear-gradient(135deg, #ffffff 0%, #f5f7f9 100%);
        box-shadow: 0 10px 30px rgba(31, 41, 51, 0.06);
      }

      .hero-kicker {
        margin: 0 0 8px;
        color: var(--cca-red);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .hero h1 {
        margin: 0;
        color: var(--ink);
        font-size: 36px;
        line-height: 1.1;
      }

      .subtitle {
        max-width: 680px;
        color: var(--muted);
        font-size: 17px;
        line-height: 1.6;
        margin: 12px 0 0;
      }

      .card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 24px rgba(31, 41, 51, 0.05);
      }

      h2 {
        color: var(--ink);
        margin: 0 0 10px;
        font-size: 24px;
      }

      .search-card {
        padding: 26px;
      }

      .search-label {
        margin: 0 0 8px;
        color: var(--ink);
        font-size: 20px;
        font-weight: 700;
      }

      .search-copy {
        margin: 0 0 18px;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.6;
      }

      ul.examples {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        color: var(--muted);
        font-size: 14px;
        margin: 0 0 18px;
        padding: 0;
        list-style: none;
      }

      ul.examples li {
        padding: 6px 10px;
        border: 1px solid var(--line-soft);
        border-radius: 999px;
        background: var(--surface-muted);
      }

      textarea {
        width: 100%;
        min-height: 128px;
        padding: 18px 18px 20px;
        font-size: 16px;
        line-height: 1.6;
        font-family: inherit;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: var(--surface-muted);
        resize: vertical;
        box-shadow: inset 0 1px 2px rgba(31, 41, 51, 0.04);
      }

      textarea:focus {
        outline: none;
        border-color: var(--cca-red);
        background: var(--surface);
        box-shadow: 0 0 0 4px rgba(154, 17, 31, 0.08);
      }

      button {
        margin-top: 14px;
        background: var(--cca-red);
        color: var(--surface);
        border: none;
        border-radius: 999px;
        padding: 12px 20px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s ease, transform 0.15s ease;
      }

      button:hover {
        background: var(--cca-red-dark);
        transform: translateY(-1px);
      }

      .response-card {
        margin-top: 32px;
        padding: 28px;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: var(--surface);
        max-width: 820px;
        box-shadow: 0 14px 32px rgba(31, 41, 51, 0.08);
      }

      .response-title {
        margin: 0 0 6px;
        color: var(--ink);
        font-size: 28px;
        font-weight: 700;
        line-height: 1.25;
      }

      .response-heading {
        display: inline-block;
        margin: 0 0 18px;
        padding: 6px 10px;
        border-radius: 999px;
        background: #F2F5F8;
        color: var(--muted);
        font-size: 14px;
        font-weight: 600;
      }

      .response-body {
        padding: 20px 22px;
        border: 1px solid var(--line-soft);
        border-radius: 18px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfcfd 100%);
        font-size: 18px;
        line-height: 1.85;
        color: var(--ink);
      }

      .response-body p {
        margin: 0 0 16px 0;
      }

      .response-body p:last-child {
        margin-bottom: 0;
      }

      .response-action {
        margin: 18px 0 0;
        padding: 16px 18px 0;
        border-top: 1px solid var(--line-soft);
        font-weight: 600;
      }

      .response-action a {
        display: inline-block;
        color: var(--cca-red);
        text-decoration: underline;
        word-break: break-word;
      }

      .response-escalation {
        margin-top: 18px;
        padding: 18px;
        border: 1px solid #E8D7DA;
        border-radius: 18px;
        background: #FFF8F8;
        font-size: 14px;
        line-height: 1.6;
        color: var(--ink);
      }

      .response-escalation h3 {
        margin: 0 0 8px;
        color: var(--cca-red-dark);
        font-size: 16px;
        font-weight: 700;
      }

      .response-escalation p {
        margin: 0 0 12px;
      }

      .response-escalation .next-step {
        color: var(--muted);
      }

      .response-escalation p:last-child {
        margin-bottom: 0;
      }

      .match-details {
        margin-top: 18px;
        padding: 14px 16px;
        border: 1px solid var(--line-soft);
        border-radius: 16px;
        background: var(--surface-muted);
      }

      .match-details h3 {
        margin: 0 0 10px;
        color: var(--muted);
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }

      .match-row {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 6px 12px;
        font-size: 14px;
        line-height: 1.5;
      }

      .match-label {
        color: var(--muted);
        font-weight: 600;
      }

      .match-value {
        color: var(--ink);
        word-break: break-word;
      }

      .response-source {
        margin-top: 14px;
        font-size: 12px;
        color: var(--muted);
      }

      .feedback-section {
        margin-top: 18px;
        padding-top: 18px;
        border-top: 1px solid var(--line-soft);
      }

      .feedback-title {
        margin: 0 0 10px;
        font-size: 14px;
        font-weight: 600;
        color: var(--ink);
      }

      .feedback-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .feedback-actions form {
        margin: 0;
      }

      .feedback-button {
        margin-top: 0;
        padding: 10px 16px;
        font-size: 14px;
        background: var(--surface-muted);
        color: var(--ink);
        border: 1px solid var(--line);
      }

      .feedback-button:hover {
        background: #EEF2F6;
      }

      .feedback-button.negative {
        background: #FFF7F7;
      }

      .feedback-thanks {
        margin-top: 18px;
        padding: 16px 18px;
        border: 1px solid #D8E4D9;
        border-radius: 16px;
        background: #F5FBF5;
        font-size: 14px;
        color: var(--ink);
      }

      @media (max-width: 720px) {
        .page {
          padding: 20px 14px 40px;
        }

        .hero,
        .card,
        .response-card {
          padding: 20px 18px;
          border-radius: 18px;
        }

        .hero h1 {
          font-size: 28px;
        }

        .subtitle {
          font-size: 15px;
        }

        h2 {
          font-size: 21px;
        }

        .search-card {
          padding: 20px 18px;
        }

        .response-title {
          font-size: 24px;
        }

        .response-body {
          padding: 16px;
          font-size: 17px;
        }

        .match-row {
          grid-template-columns: 1fr;
          gap: 2px 0;
        }

        .match-label {
          margin-top: 8px;
        }

        .feedback-actions {
          flex-direction: column;
        }

        .feedback-actions form,
        .feedback-button {
          width: 100%;
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <div class="hero">
        <p class="hero-kicker">Student Support</p>
        <h1>CCA IT Support Assistant</h1>
        <p class="subtitle">
          Get quick help for common campus technology questions using official Community College of Aurora IT guidance.
        </p>
      </div>

      <div class="card search-card">
        <div class="search-label">Ask a question</div>
        <p class="search-copy">
          Search for help with passwords, email, Wi-Fi, D2L, Zoom, and other common student IT needs.
        </p>
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
                  <button class="feedback-button negative" type="submit">No, I still need help</button>
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
