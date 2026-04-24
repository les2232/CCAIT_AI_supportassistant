import argparse
import csv
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "it_help_logs.db"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "exports"

UNSUPPORTED_FILENAME = "unsupported_topics.csv"
ESCALATIONS_FILENAME = "escalations.csv"
DOC_UNAVAILABLE_FILENAME = "documentation_unavailable.csv"


def resolve_args() -> argparse.Namespace:
    """Resolve command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export Phase 3 review CSVs from the IT help log database."
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the SQLite database file. Defaults to it_help_logs.db.",
    )
    parser.add_argument(
        "--outdir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where CSV exports will be written.",
    )
    return parser.parse_args()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def write_query_to_csv(conn: sqlite3.Connection, query: str, output_path: Path) -> int:
    """Run a query and write all results to a CSV file."""
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    fieldnames = [column[0] for column in cursor.description]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    return len(rows)


def main() -> None:
    args = resolve_args()
    db_path = Path(args.db).resolve()
    output_dir = Path(args.outdir).resolve()

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Run the app first or seed the test database before exporting.")
        return

    queries = {
        UNSUPPORTED_FILENAME: """
            SELECT
                created_at,
                raw_question,
                routed_topic,
                article_id,
                supported,
                escalation_flag,
                response_type
            FROM request_logs
            WHERE supported = 0
            ORDER BY created_at DESC, raw_question ASC
        """,
        ESCALATIONS_FILENAME: """
            SELECT
                created_at,
                raw_question,
                routed_topic,
                article_id,
                supported,
                escalation_flag,
                response_type
            FROM request_logs
            WHERE escalation_flag = 1
            ORDER BY created_at DESC, routed_topic ASC
        """,
        DOC_UNAVAILABLE_FILENAME: """
            SELECT
                created_at,
                raw_question,
                routed_topic,
                article_id,
                supported,
                escalation_flag,
                response_type
            FROM request_logs
            WHERE response_type = 'documentation_unavailable'
            ORDER BY created_at DESC, routed_topic ASC
        """,
    }

    with get_connection(db_path) as conn:
        for filename, query in queries.items():
            output_path = output_dir / filename
            row_count = write_query_to_csv(conn, query, output_path)
            print(f"Wrote {row_count} rows to {output_path}")


if __name__ == "__main__":
    main()
