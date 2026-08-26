import pytest


@pytest.mark.functional
def test_idn_returns_identification_string(scpi_client):
    response = scpi_client.query("*IDN?")
    assert response == "NetTest,MockPhotonicsInstrument,SN001,FW1.0"


@pytest.mark.functional
def test_reset_leaves_instrument_responsive(scpi_client):
    scpi_client.send_command("*RST")
    response = scpi_client.query("MEAS:VOLT?")
    assert response


@pytest.mark.functional
def test_syst_err_reports_no_error_initially(scpi_client):
    response = scpi_client.query("SYST:ERR?")
    assert response == "0,No error"


@pytest.mark.regression
def test_measure_voltage_returns_volts_not_millivolts(scpi_client):
    response = scpi_client.query("MEAS:VOLT?")
    assert response == "3.300"


@pytest.mark.regression
def test_unknown_command_is_logged_to_error_queue(scpi_client):
    scpi_client.send_command("FOO:BAR?")
    response = scpi_client.query("SYST:ERR?")
    assert response != "0,No error"
