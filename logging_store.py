import sqlite3
from datetime import UTC, datetime
from pathlib import Path


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
                response_type,
                llm_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                question,
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
