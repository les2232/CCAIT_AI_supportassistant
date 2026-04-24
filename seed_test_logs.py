import argparse
import sqlite3
from datetime import datetime, UTC, timedelta
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "it_help_logs_test.db"
REAL_DB_NAME = "it_help_logs.db"

SAMPLE_LOGS = [
    {
        "days_ago": 0,
        "raw_question": "How do I reset my password?",
        "routed_topic": "password-reset.txt",
        "article_id": "password-reset.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 0,
        "raw_question": "Wi-Fi keeps dropping on my laptop",
        "routed_topic": "wifi-troubleshooting.txt",
        "article_id": "wifi-troubleshooting.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 0,
        "raw_question": "How do I log into my student email?",
        "routed_topic": "student-email.txt",
        "article_id": "student-email.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 1,
        "raw_question": "Where do I submit assignments?",
        "routed_topic": "canvas-mycourses.txt",
        "article_id": "canvas-mycourses.txt",
        "supported": 1,
        "escalation_flag": 0,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 1,
        "raw_question": "My MyCCA login is not working",
        "routed_topic": "password-reset.txt",
        "article_id": "password-reset.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 1,
        "raw_question": "How do I get a semester laptop?",
        "routed_topic": None,
        "article_id": None,
        "supported": 0,
        "escalation_flag": 0,
        "response_type": "unsupported_topic",
    },
    {
        "days_ago": 2,
        "raw_question": "Can I borrow a calculator?",
        "routed_topic": None,
        "article_id": None,
        "supported": 0,
        "escalation_flag": 0,
        "response_type": "unsupported_topic",
    },
    {
        "days_ago": 2,
        "raw_question": "Student email setup",
        "routed_topic": "student-email.txt",
        "article_id": "student-email.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 3,
        "raw_question": "The Wi-Fi says connected but no internet",
        "routed_topic": "wifi-troubleshooting.txt",
        "article_id": "wifi-troubleshooting.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 3,
        "raw_question": "How do I find my school email address?",
        "routed_topic": "student-email.txt",
        "article_id": "student-email.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 4,
        "raw_question": "Parking permit help",
        "routed_topic": None,
        "article_id": None,
        "supported": 0,
        "escalation_flag": 0,
        "response_type": "unsupported_topic",
    },
    {
        "days_ago": 4,
        "raw_question": "How do I join CCAStudents Wi-Fi?",
        "routed_topic": "wifi-troubleshooting.txt",
        "article_id": "wifi-troubleshooting.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 5,
        "raw_question": "Blank input test",
        "routed_topic": None,
        "article_id": None,
        "supported": 0,
        "escalation_flag": 0,
        "response_type": "unsupported_topic",
    },
    {
        "days_ago": 5,
        "raw_question": "How do I submit homework in D2L?",
        "routed_topic": "canvas-mycourses.txt",
        "article_id": "canvas-mycourses.txt",
        "supported": 1,
        "escalation_flag": 0,
        "response_type": "documentation_article",
    },
    {
        "days_ago": 6,
        "raw_question": "Office login help",
        "routed_topic": "student-email.txt",
        "article_id": "student-email.txt",
        "supported": 1,
        "escalation_flag": 1,
        "response_type": "documentation_article",
    },
]


def resolve_args() -> argparse.Namespace:
    """Resolve command-line arguments."""
    parser = argparse.ArgumentParser(description="Seed sample IT help logs into a test database.")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the SQLite database file. Defaults to it_help_logs_test.db.",
    )
    parser.add_argument(
        "--allow-real-db",
        action="store_true",
        help="Allow writes to it_help_logs.db.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append sample data instead of clearing existing request_logs rows first.",
    )
    return parser.parse_args()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection."""
    return sqlite3.connect(db_path)


def init_logging_db(conn: sqlite3.Connection) -> None:
    """Create the request_logs table if needed."""
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
    conn.commit()


def enforce_db_safety(db_path: Path, allow_real_db: bool) -> None:
    """Prevent accidental writes to the real application database."""
    if db_path.name == REAL_DB_NAME and not allow_real_db:
        raise SystemExit(
            "Refusing to write seed data to it_help_logs.db.\n"
            "Use the default test database or pass --allow-real-db explicitly."
        )


def build_sample_rows() -> list[tuple]:
    """Build sample rows with realistic timestamps."""
    base_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    rows = []
    for index, item in enumerate(SAMPLE_LOGS):
        created_at = base_time - timedelta(days=item["days_ago"], hours=index % 4)
        rows.append(
            (
                created_at.isoformat(),
                item["raw_question"],
                item["routed_topic"],
                item["article_id"],
                item["supported"],
                item["escalation_flag"],
                item["response_type"],
            )
        )
    return rows


def main() -> None:
    args = resolve_args()
    db_path = Path(args.db).resolve()
    enforce_db_safety(db_path, args.allow_real_db)

    with get_connection(db_path) as conn:
        init_logging_db(conn)

        if not args.append:
            conn.execute("DELETE FROM request_logs")

        conn.executemany(
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
            build_sample_rows(),
        )
        conn.commit()

    print(f"Seeded {len(SAMPLE_LOGS)} sample rows into {db_path}")


if __name__ == "__main__":
    main()
