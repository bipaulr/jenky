Private notes — not linked from README. Ground truth for the "Bugs Caught"
section.

## Bug 1: MEAS:VOLT? returns millivolts formatted as volts

`scpi_sim/server.py`, `Instrument.measure_voltage()`.

`return self.voltage * 1000` multiplies the stored value (already in
volts) by 1000 before it's formatted with `.3f`, so a 3.3V reading comes
back as `"3300.000"` instead of `"3.300"` — a unit-conversion bug, not a
formatting bug.

Caught by: `tests/test_scpi_instrument.py::test_measure_voltage_returns_volts_not_millivolts`

## Bug 2: unknown commands never reach the error queue

`scpi_sim/server.py`, `handle_command()`.

The fallback branch for an unrecognized command returns `None` without
calling `instrument.push_error(...)`. A real SCPI instrument enqueues an
error (e.g. `-113,"Undefined header"`) that `SYST:ERR?` should later
report. Here, sending garbage silently succeeds and a subsequent
`SYST:ERR?` still reports `"0,No error"`.

Caught by: `tests/test_scpi_instrument.py::test_unknown_command_is_logged_to_error_queue`
