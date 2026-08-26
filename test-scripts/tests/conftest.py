import threading
import uuid
from datetime import datetime, timezone

import pytest
from werkzeug.serving import make_server

from app.server import create_app
from reporting.db import finish_run, get_connection, log_result, start_run
from scpi_sim.client import SCPIClient
from scpi_sim.server import create_server


class ServerThread(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 0, app)
        self.port = self.server.server_port

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture
def api_base_url():
    app = create_app()
    thread = ServerThread(app)
    thread.start()
    yield f"http://127.0.0.1:{thread.port}"
    thread.shutdown()
    thread.join(timeout=5)


class SCPIServerThread(threading.Thread):
    def __init__(self, server):
        super().__init__(daemon=True)
        self.server = server

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def scpi_client():
    server = create_server()
    thread = SCPIServerThread(server)
    thread.start()
    host, port = server.server_address
    client = SCPIClient(host, port)
    yield client
    client.close()
    thread.shutdown()
    thread.join(timeout=5)


def pytest_sessionstart(session):
    session.config.nettest_run_id = uuid.uuid4().hex
    session.config.nettest_conn = get_connection()
    start_run(
        session.config.nettest_conn,
        session.config.nettest_run_id,
        datetime.now(timezone.utc).isoformat(),
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.when == "setup" and report.failed):
        return
    conn = item.config.nettest_conn
    run_id = item.config.nettest_run_id
    error_message = str(report.longrepr) if report.failed else None
    log_result(
        conn,
        run_id,
        item.nodeid,
        ",".join(marker.name for marker in item.iter_markers()),
        report.outcome,
        report.duration * 1000,
        error_message,
        datetime.now(timezone.utc).isoformat(),
    )


def pytest_sessionfinish(session, exitstatus):
    conn = session.config.nettest_conn
    finish_run(conn, session.config.nettest_run_id, datetime.now(timezone.utc).isoformat())
    conn.close()
