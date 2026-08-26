# Changelog

## test-suite-v0.1.3

- Demo for Phase 6 (rollback): adds the SIMULATE_SMOKE_FAILURE marker file,
  a deliberate, documented trigger (see scripts/smoke_check.sh) for the
  post-promotion smoke check to fail on purpose, so the automatic rollback
  path can be exercised for real. Not a real defect, and not something the
  full pytest suite catches - by design, that's the whole reason the
  marker exists.

## test-suite-v0.1.2

- Add `test_delete_missing_device_returns_404`, covering a previously
  untested edge case (deleting a nonexistent device). Demonstrates a
  properly versioned, PR-reviewed change for the Jenky change-control gate
  (Phase 4).

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
