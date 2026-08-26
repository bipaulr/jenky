import pytest

from l2.frame_validation import build_ipv4_frame, parse_ethernet_header, validate_ipv4_checksum


@pytest.mark.functional
def test_ethernet_header_fields_round_trip():
    frame = build_ipv4_frame(src_mac="02:00:00:00:00:01", dst_mac="02:00:00:00:00:02")
    header = parse_ethernet_header(frame)
    assert header["src_mac"] == "02:00:00:00:00:01"
    assert header["dst_mac"] == "02:00:00:00:00:02"
    assert header["ethertype"] == 0x0800


@pytest.mark.functional
def test_valid_frame_passes_checksum_validation():
    frame = build_ipv4_frame()
    assert validate_ipv4_checksum(frame) is True


@pytest.mark.regression
def test_corrupted_checksum_is_rejected():
    frame = bytearray(build_ipv4_frame())
    frame[24] ^= 0xFF
    assert validate_ipv4_checksum(bytes(frame)) is False


@pytest.mark.regression
def test_truncated_frame_is_rejected():
    frame = build_ipv4_frame()[:10]
    assert validate_ipv4_checksum(frame) is False
