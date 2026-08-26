import struct

from scapy.layers.inet import IP, Ether

ETHERNET_HEADER_LEN = 14
IPV4_HEADER_LEN = 20


def build_ipv4_frame(
    src_mac="02:00:00:00:00:01",
    dst_mac="02:00:00:00:00:02",
    src_ip="10.0.0.1",
    dst_ip="10.0.0.2",
    payload=b"NETTEST",
):
    packet = Ether(src=src_mac, dst=dst_mac) / IP(src=src_ip, dst=dst_ip) / payload
    return bytes(packet)


def parse_ethernet_header(frame_bytes):
    if len(frame_bytes) < ETHERNET_HEADER_LEN:
        raise ValueError("frame is shorter than an Ethernet header")
    dst_mac = frame_bytes[0:6]
    src_mac = frame_bytes[6:12]
    ethertype = struct.unpack("!H", frame_bytes[12:14])[0]
    return {
        "dst_mac": ":".join(f"{b:02x}" for b in dst_mac),
        "src_mac": ":".join(f"{b:02x}" for b in src_mac),
        "ethertype": ethertype,
    }


def _internet_checksum(data):
    if len(data) % 2 == 1:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    total = (total & 0xFFFF) + (total >> 16)
    total += total >> 16
    return (~total) & 0xFFFF


def validate_ipv4_checksum(frame_bytes):
    """Independently recomputes the IPv4 header checksum from raw wire
    bytes and compares it to the checksum field, rather than trusting
    whatever tool produced the frame."""
    ip_header = frame_bytes[ETHERNET_HEADER_LEN:ETHERNET_HEADER_LEN + IPV4_HEADER_LEN]
    if len(ip_header) < IPV4_HEADER_LEN:
        return False
    stored_checksum = struct.unpack("!H", ip_header[10:12])[0]
    header_with_zeroed_checksum = ip_header[:10] + b"\x00\x00" + ip_header[12:]
    return _internet_checksum(header_with_zeroed_checksum) == stored_checksum
