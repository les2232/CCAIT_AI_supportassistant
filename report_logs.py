import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "it_help_logs.db"


def resolve_db_path() -> Path:
    """Resolve the database path from CLI arguments."""
    parser = argparse.ArgumentParser(description="Run internal reports for IT help logs.")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the SQLite database file. Defaults to it_help_logs.db.",
    )
    args = parser.parse_args()
    return Path(args.db).resolve()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_one_value(cursor: sqlite3.Cursor, query: str, params: tuple = ()) -> int:
    """Run a query expected to return a single numeric value."""
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row is None:
        return 0
    return row[0] if row[0] is not None else 0


def print_section(title: str) -> None:
    """Print a report section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    db_path = resolve_db_path()

    if not db_path.exists():
        print(f"Database not found: {db_path.resolve()}")
        print("Run the app first so request logs are created.")
        return

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        print_section("CCA AI IT Help Assistant — Internal Request Report")

        total_requests = fetch_one_value(
            cursor,
            "SELECT COUNT(*) FROM request_logs"
        )

        supported_requests = fetch_one_value(
            cursor,
            "SELECT COUNT(*) FROM request_logs WHERE supported = 1"
        )

        unsupported_requests = fetch_one_value(
            cursor,
            "SELECT COUNT(*) FROM request_logs WHERE supported = 0"
        )

        escalations = fetch_one_value(
            cursor,
            "SELECT COUNT(*) FROM request_logs WHERE escalation_flag = 1"
        )

        doc_unavailable = fetch_one_value(
            cursor,
            """
            SELECT COUNT(*)
            FROM request_logs
            WHERE response_type = 'documentation_unavailable'
            """
        )

        unsupported_rate = (
            (unsupported_requests / total_requests) * 100
            if total_requests > 0 else 0.0
        )

        escalation_rate = (
            (escalations / total_requests) * 100
            if total_requests > 0 else 0.0
        )

        print(f"Total requests:                  {total_requests}")
        print(f"Supported requests:              {supported_requests}")
        print(f"Unsupported requests:            {unsupported_requests}")
        print(f"Unsupported rate:                {unsupported_rate:.1f}%")
        print(f"Escalations:                     {escalations}")
        print(f"Escalation rate:                 {escalation_rate:.1f}%")
        print(f"Documentation unavailable:       {doc_unavailable}")

        print_section("Top Routed Topics")

        cursor.execute(
            """
            SELECT routed_topic, COUNT(*) AS total
            FROM request_logs
            WHERE routed_topic IS NOT NULL AND routed_topic != ''
            GROUP BY routed_topic
            ORDER BY total DESC, routed_topic ASC
            LIMIT 10
            """
        )
        topic_rows = cursor.fetchall()

        if not topic_rows:
            print("No routed topics logged yet.")
        else:
            for row in topic_rows:
                print(f"{row['routed_topic']}: {row['total']}")

        print_section("Unsupported Topic Patterns")

        cursor.execute(
            """
            SELECT raw_question, COUNT(*) AS total
            FROM request_logs
            WHERE supported = 0
            GROUP BY raw_question
            ORDER BY total DESC, raw_question ASC
            LIMIT 10
            """
        )
        unsupported_rows = cursor.fetchall()

        if not unsupported_rows:
            print("No unsupported questions logged yet.")
        else:
            for row in unsupported_rows:
                print(f"{row['total']}x - {row['raw_question']}")

        print_section("Documentation Gaps")

        cursor.execute(
            """
            SELECT routed_topic, COUNT(*) AS total
            FROM request_logs
            WHERE response_type = 'documentation_unavailable'
            GROUP BY routed_topic
            ORDER BY total DESC, routed_topic ASC
            """
        )
        gap_rows = cursor.fetchall()

        if not gap_rows:
            print("No documentation-unavailable cases logged yet.")
        else:
            for row in gap_rows:
                topic = row["routed_topic"] if row["routed_topic"] else "(unclassified)"
                print(f"{topic}: {row['total']}")

        print_section("Recent Escalations")

        cursor.execute(
            """
            SELECT created_at, raw_question, routed_topic, response_type
            FROM request_logs
            WHERE escalation_flag = 1
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
        escalation_rows = cursor.fetchall()

        if not escalation_rows:
            print("No escalations logged yet.")
        else:
            for row in escalation_rows:
                topic = row["routed_topic"] if row["routed_topic"] else "(none)"
                print(f"[{row['created_at']}] {topic} | {row['response_type']}")
                print(f"  {row['raw_question']}")

        print_section("Daily Volume")

        cursor.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS total
            FROM request_logs
            GROUP BY day
            ORDER BY day DESC
            LIMIT 14
            """
        )
        volume_rows = cursor.fetchall()

        if not volume_rows:
            print("No daily volume data yet.")
        else:
            for row in volume_rows:
                print(f"{row['day']}: {row['total']}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
