# NetTest

A Python test automation framework built to demonstrate the testing
*methodology* for a network/instrument test automation role — functional
and regression testing, hardware-protocol communication, result logging,
and CI-driven change control — using honestly-labeled simulations where
real lab hardware wasn't available.

**Status:** Complete, at trimmed scope (see "Cut from this build" below).
17 tests passing across three subsystems, all wired through shared SQLite
logging, HTML + CLI reporting, and a Jenkins pipeline verified with a real
local run.

## What this demonstrates

| Area | Where |
|---|---|
| Functional + regression testing | `tests/test_api_functional.py`, `tests/test_api_regression.py` |
| Hardware communication protocol (SCPI, TCP/IP) | `scpi_sim/server.py`, `scpi_sim/client.py`, `tests/test_scpi_instrument.py` |
| Layer 1/2 network validation | `l2/frame_validation.py`, `tests/test_l2_frames.py` |
| SQL-based result logging | `reporting/db.py`, `tests/conftest.py` (pytest hooks — no test calls the DB directly) |
| CI/CD | `Jenkinsfile`, verified with a real local Jenkins run (`docs/jenkins-build-4-console.txt`) |
| Change control for test scripts | `CHANGELOG.md` + git tags (`test-suite-v0.1.0`) |

## Architecture

Three independent subsystems under test — a REST API (`app/`), a mock
SCPI-over-TCP instrument (`scpi_sim/`), and a Layer 2 frame validator
(`l2/`) — each with its own pytest test file. Every test run, regardless
of which subsystem it targets, is captured by the same `conftest.py`
pytest hooks and written to a single SQLite database
(`results/test_results.db`) with no test file ever touching the database
directly. `reporting/summary.py` queries that database for a pass/fail
trend CLI, and `pytest-html` produces a self-contained HTML report. The
`Jenkinsfile` runs all of this — checkout, fresh venv, install, test,
publish — and archives the HTML report, the trend summary, and the SQLite
DB as build artifacts.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
pytest --html=report.html --self-contained-html -v
python -m reporting.summary
```

Run everything: `pytest -v`. Just the regression suites (the ones that
pin down the seeded bugs below): `pytest -m regression -v`.

## What's simulated vs. real

| Component | Status |
|---|---|
| REST API (`app/`) | Real — a real Flask app, real HTTP over a real socket, run in a background thread per test for isolation. |
| SCPI instrument (`scpi_sim/`) | **Simulated.** A hand-rolled, line-based TCP socket server implementing a small SCPI-like command subset (`*IDN?`, `*RST`, `MEAS:VOLT?`, `SYST:ERR?`). No VISA library, no physical bus (GPIB/RS-232/USB), no real instrument. Chosen deliberately over the pyvisa/pyvisa-py route to keep the deliverable low-friction under a hard deadline — see "Cut from this build." |
| Layer 2 validation (`l2/`) | **Simulated.** Frames are constructed and parsed entirely in memory via scapy (`Ether()/IP()/...`); nothing is sent or sniffed on a real NIC. No traffic-generator (e.g. IXIA) hardware involved — this demonstrates the frame-validation methodology such hardware's output would need to satisfy, not IXIA usage itself. |
| CI/CD | Real Jenkins, run locally once and verified (see below). ArgoCD is not implemented — it's a GitOps tool for Kubernetes, out of scope for a solo local project. Change control here is Jenkins + git tags instead; see `CHANGELOG.md`. |

## Bugs caught

Each bug below was seeded deliberately, confirmed to make its regression
test fail, then fixed and confirmed green — a real red-to-green loop, not
a retrofitted test suite.

| # | Bug | Caught by | Fix |
|---|---|---|---|
| 1 | `GET /devices` pagination dropped the last item on a full page (`end = start + per_page - 1`, an off-by-one on an exclusive slice bound) | `test_pagination_does_not_drop_last_item_on_page` | `end = start + per_page` |
| 2 | `GET /devices/<id>` for a missing device returned `200 {}` instead of `404` — a client couldn't tell "empty device" from "no such device" | `test_get_missing_device_returns_404` | Return `404` with an error body when the device isn't found |
| 3 | `POST /devices` accepted a device with no `ip_address`, silently storing `None` | `test_create_device_requires_ip_address` | Require and validate `ip_address`, return `400` if missing |
| 4 | Mock SCPI instrument's `MEAS:VOLT?` multiplied the stored voltage by 1000 before formatting — a unit-conversion bug, returning `"3300.000"` instead of `"3.300"` | `test_measure_voltage_returns_volts_not_millivolts` | Return the stored value directly, no spurious conversion |
| 5 | Mock SCPI instrument silently dropped unrecognized commands instead of enqueuing an error — `SYST:ERR?` always reported `"0,No error"` even after garbage input | `test_unknown_command_is_logged_to_error_queue` | Push `(-113, "Undefined header")` onto the error queue for unrecognized commands |

## Jenkins pipeline

`Jenkinsfile` runs Checkout -> Setup -> Test -> Publish and archives
`report.html`, `summary.txt`, and the SQLite results DB as build
artifacts. Verified with a real local Jenkins instance (`jenkins.war`,
run outside this repo, not committed) against a fresh clone of this
repository — all tests passed independently of the developer's own venv.
Console log for that run: [docs/jenkins-build-4-console.txt](docs/jenkins-build-4-console.txt).

Not run continuously — this is a local, one-shot CI verification, not a
hosted server. To reproduce:

```bash
java -Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true -jar jenkins.war --httpPort=8080
```

(`ALLOW_LOCAL_CHECKOUT` is only needed because this demo checks out from
a local filesystem path rather than a remote git host — Jenkins' git
plugin blocks local-path checkouts by default as a security measure.)

## Change control for test scripts

Test-script releases are tagged in git (`test-suite-v0.1.0`, ...) with a
matching entry in `CHANGELOG.md` describing what changed and why — a
lightweight, solo-appropriate stand-in for a multi-reviewer approval gate.

## Cut from this build

Trimmed deliberately to hit a hard deadline. Not reintroduced without it
being asked for:

- **pyvisa/pyvisa-py upgrade** for the SCPI simulator — shipped the
  hand-rolled socket server instead.
- **Live/persistent Jenkins demo** — the pipeline was verified with one
  real local run (evidence above), not kept running as a hosted server.
- **Link-status mock** in the L2 module — only frame construction and
  checksum validation were built.
- **Allure reporting** — `pytest-html` only.
- **Architecture diagram** — prose summary above instead.

## Repo layout

```
nettester/
├── README.md
├── requirements.txt
├── .gitignore
├── Jenkinsfile
├── CHANGELOG.md
├── pytest.ini
├── app/                    # REST API under test (3 seeded bugs)
│   ├── server.py
│   └── seeded_bugs.md
├── scpi_sim/                # mock SCPI-over-TCP instrument (2 seeded bugs)
│   ├── server.py
│   └── client.py
├── l2/                       # Layer 2 frame construction + checksum validation
│   └── frame_validation.py
├── reporting/
│   ├── db.py                # SQLite schema + helpers
│   └── summary.py           # pass/fail trend CLI
├── tests/
│   ├── conftest.py          # server fixtures + DB logging hooks
│   ├── test_api_functional.py
│   ├── test_api_regression.py
│   ├── test_scpi_instrument.py
│   └── test_l2_frames.py
├── docs/
│   └── jenkins-build-4-console.txt
└── results/                 # generated, gitignored
    └── test_results.db
```

## Two-minute walkthrough

This project demonstrates the test automation workflow this kind of role
needs, built without lab hardware access. A Flask REST API and a mock
SCPI-over-TCP instrument both ship with real, deliberately seeded bugs,
tested with a pytest suite split into functional and regression tests —
every regression test was confirmed to fail against its bug before the
fix landed. Every test run, across all three subsystems, logs to SQLite
through pytest hooks with zero manual logging calls inside any test file,
and a small CLI queries pass/fail trends across runs. A Layer 2 module
built on scapy constructs and validates Ethernet/IPv4 frames with an
independent checksum verifier, catching both corrupted and truncated
frames. The whole suite runs through a Jenkins pipeline — verified with a
real local run that cloned the repo fresh and reproduced everything
independently — with test-script versions tagged in git as a lightweight
change-control process. Everything hardware-adjacent is labeled
accordingly: the SCPI server and the L2 module are both simulated, no
real instrument, VISA library, or NIC access involved.
