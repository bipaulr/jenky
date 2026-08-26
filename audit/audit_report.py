import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "test-scripts" / "results" / "test_results.db"


def print_table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT build_number, script_version, substr(git_commit_sha, 1, 8),
               triggered_by, timestamp, test_outcome, gate_outcome, gate_reason
        FROM audit_log
        ORDER BY build_number
        """
    ).fetchall()
    conn.close()

    if not rows:
        print("No audit log entries yet. Run the pipeline first.")
        return

    print_table(
        ["build", "version", "commit", "triggered_by", "timestamp", "tests", "gate", "gate_reason"],
        rows,
    )


if __name__ == "__main__":
    main()
