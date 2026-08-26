import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "test-scripts" / "results" / "test_results.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    build_number INTEGER PRIMARY KEY,
    script_version TEXT NOT NULL,
    git_commit_sha TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    test_outcome TEXT NOT NULL,
    gate_outcome TEXT NOT NULL,
    gate_reason TEXT
);
"""


def record(build_number, version, commit_sha, author, test_outcome, gate_outcome, gate_reason):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute(
        """INSERT OR REPLACE INTO audit_log
           (build_number, script_version, git_commit_sha, triggered_by, timestamp,
            test_outcome, gate_outcome, gate_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            build_number,
            version,
            commit_sha,
            author,
            datetime.now(timezone.utc).isoformat(),
            test_outcome,
            gate_outcome,
            gate_reason,
        ),
    )
    conn.commit()
    conn.close()


REQUIRED_VARS = ["BUILD_NUMBER", "SCRIPT_VERSION", "GIT_COMMIT", "COMMIT_AUTHOR", "TEST_OUTCOME"]


def main():
    missing = [name for name in REQUIRED_VARS if not os.environ.get(name)]
    if missing:
        print(f"missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    build_number = int(os.environ["BUILD_NUMBER"])
    record(
        build_number,
        os.environ["SCRIPT_VERSION"],
        os.environ["GIT_COMMIT"],
        os.environ["COMMIT_AUTHOR"],
        os.environ["TEST_OUTCOME"],
        os.environ.get("GATE_OUTCOME", "not_evaluated"),
        os.environ.get("GATE_REASON", ""),
    )
    print(f"Audit log recorded for build #{build_number}: "
          f"version={os.environ['SCRIPT_VERSION']} gate={os.environ.get('GATE_OUTCOME', 'not_evaluated')}")


if __name__ == "__main__":
    main()
