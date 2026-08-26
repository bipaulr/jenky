# Changelog

## test-suite-v0.1.1

- Bumped to verify the Jenkins pipeline's version stamping (Phase 3 of the
  Jenky wrapper): no test-script behavior changed.

## test-suite-v0.1.0

- REST API target (`app/`) with 3 seeded bugs (pagination off-by-one,
  missing-device 200 instead of 404, POST accepting no `ip_address`) and a
  functional + regression pytest suite (`tests/test_api_functional.py`,
  `tests/test_api_regression.py`).
- SQLite result logging via pytest hooks (`tests/conftest.py`,
  `reporting/db.py`) — no manual logging calls inside test files.
- HTML reporting (`pytest-html`) and a DB-backed pass/fail trend CLI
  (`reporting/summary.py`).
- Mock SCPI-over-TCP instrument (`scpi_sim/`) implementing `*IDN?`,
  `*RST`, `MEAS:VOLT?`, `SYST:ERR?` with 2 seeded bugs (voltage unit
  conversion, dropped error-queue entries) and its own regression suite
  (`tests/test_scpi_instrument.py`).
- `Jenkinsfile`: Checkout -> Setup -> Test -> Publish, archiving
  `report.html`, `summary.txt`, and the SQLite results DB as build
  artifacts.
