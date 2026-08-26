import sqlite3

from reporting.db import get_connection


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


def latest_run_id(conn):
    row = conn.execute(
        "SELECT run_id FROM test_runs ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def pass_rate_by_marker(conn, run_id):
    return conn.execute(
        """
        SELECT markers,
               SUM(CASE WHEN outcome = 'passed' THEN 1 ELSE 0 END) AS passed,
               COUNT(*) AS total
        FROM results
        WHERE run_id = ?
        GROUP BY markers
        ORDER BY markers
        """,
        (run_id,),
    ).fetchall()


def slowest_tests(conn, run_id, limit=5):
    return conn.execute(
        """
        SELECT test_name, ROUND(duration_ms, 1)
        FROM results
        WHERE run_id = ?
        ORDER BY duration_ms DESC
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()


def failed_tests(conn, run_id):
    return conn.execute(
        """
        SELECT test_name, error_message
        FROM results
        WHERE run_id = ? AND outcome = 'failed'
        """,
        (run_id,),
    ).fetchall()


def run_trend(conn):
    return conn.execute(
        """
        SELECT test_runs.run_id,
               test_runs.started_at,
               SUM(CASE WHEN results.outcome = 'passed' THEN 1 ELSE 0 END) AS passed,
               SUM(CASE WHEN results.outcome = 'failed' THEN 1 ELSE 0 END) AS failed,
               COUNT(*) AS total
        FROM test_runs
        JOIN results ON results.run_id = test_runs.run_id
        GROUP BY test_runs.run_id
        ORDER BY test_runs.started_at
        """
    ).fetchall()


def main():
    conn = get_connection()
    run_id = latest_run_id(conn)
    if run_id is None:
        print("No test runs logged yet. Run pytest first.")
        return

    print(f"Latest run: {run_id}\n")

    print("Pass rate by marker")
    print_table(
        ["markers", "passed", "total"],
        pass_rate_by_marker(conn, run_id),
    )

    print("\nSlowest tests")
    print_table(["test_name", "duration_ms"], slowest_tests(conn, run_id))

    failures = failed_tests(conn, run_id)
    if failures:
        print("\nFailed tests")
        print_table(["test_name", "error_message"], failures)

    print("\nRun trend")
    print_table(
        ["run_id", "started_at", "passed", "failed", "total"],
        run_trend(conn),
    )

    conn.close()


if __name__ == "__main__":
    main()
