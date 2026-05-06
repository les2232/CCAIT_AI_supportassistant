import sqlite3
import os
import re
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).parent / "it_help_logs.db"
LOG_DB_PATH_ENV = "IT_SUPPORT_LOG_DB_PATH"


SENSITIVE_LOG_PATTERNS = (
    (
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[redacted-email]",
    ),
    (
        re.compile(
            r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
        ),
        "[redacted-phone]",
    ),
    (
        re.compile(r"\bS\d{8}\b", re.IGNORECASE),
        "[redacted-student-id]",
    ),
    (
        re.compile(
            r"(?i)\b(password|passcode)\s*(?:is|=|:)?\s*([^\s,;]+)"
        ),
        r"\1 [redacted-password]",
    ),
    (
        re.compile(
            r"(?i)\b((?:mfa|verification|authenticator)\s*(?:code)?)\s*(?:is|=|:)?\s*(\d{4,8})"
        ),
        r"\1 [redacted-code]",
    ),
)


def redact_sensitive_log_text(value):
    """
    Redact obvious secrets and personal identifiers before writing support logs.
    """
    if value is None:
        return None

    text = str(value)
    for pattern, replacement in SENSITIVE_LOG_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def get_log_db_path():
    """
    Return the configured SQLite logging path.
    Defaults to the project-local development database.
    """
    raw_path = os.environ.get(LOG_DB_PATH_ENV, "").strip()
    if not raw_path:
        return DEFAULT_DB_PATH
    return Path(raw_path).expanduser()


def connect_logging_db():
    """
    Open the logging database, creating the parent directory when possible.
    """
    db_path = get_log_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_logging_db():
    """
    Initialize the SQLite logging database.
    """
    with connect_logging_db() as conn:
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
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(request_logs)").fetchall()
        }
        if "llm_used" not in existing_columns:
            conn.execute(
                """
                ALTER TABLE request_logs
                ADD COLUMN llm_used INTEGER NOT NULL DEFAULT 0
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


def log_request(
    question,
    routed_topic,
    supported,
    escalation_flag,
    response_type,
    article_id=None,
    llm_used=False,
):
    """
    Insert one request log record.
    """
    with connect_logging_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO request_logs (
                created_at,
                raw_question,
                routed_topic,
                article_id,
                supported,
                escalation_flag,
                response_type,
                llm_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                redact_sensitive_log_text(question),
                routed_topic,
                article_id,
                int(supported),
                int(escalation_flag),
                response_type,
                int(llm_used),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def log_feedback(request_log_id, helpful, comment=None):
    """
    Insert one feedback log record.
    """
    with connect_logging_db() as conn:
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
                redact_sensitive_log_text(comment),
            ),
        )
        conn.commit()
