import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "results" / "test_results.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    markers TEXT,
    outcome TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    error_message TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
);
"""


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def start_run(conn, run_id, started_at):
    conn.execute(
        "INSERT INTO test_runs (run_id, started_at) VALUES (?, ?)",
        (run_id, started_at),
    )
    conn.commit()


def finish_run(conn, run_id, finished_at):
    conn.execute(
        "UPDATE test_runs SET finished_at = ? WHERE run_id = ?",
        (finished_at, run_id),
    )
    conn.commit()


def log_result(conn, run_id, test_name, markers, outcome, duration_ms, error_message, timestamp):
    conn.execute(
        """INSERT INTO results
           (run_id, test_name, markers, outcome, duration_ms, error_message, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, test_name, markers, outcome, duration_ms, error_message, timestamp),
    )
    conn.commit()
