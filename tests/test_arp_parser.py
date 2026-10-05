from netwatch.scanner import DiscoveredDevice, parse_arp_output

WINDOWS = """
Interface: 192.168.1.10 --- 0xb
  Internet Address      Physical Address      Type
  192.168.1.1           a4-2b-b0-12-34-56     dynamic
  192.168.1.23          3C-22-FB-AA-BB-CC     dynamic
  192.168.1.255         ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
"""

MACOS = """
? (192.168.1.1) at a4:2b:b0:12:34:56 on en0 ifscope [ethernet]
? (192.168.1.40) at 0:1b:63:a:b:c on en0 ifscope [ethernet]
? (192.168.1.99) at (incomplete) on en0 ifscope [ethernet]
"""

PROC_NET_ARP = """\
IP address       HW type     Flags       HW address            Mask     Device
192.168.1.1      0x1         0x2         a4:2b:b0:12:34:56     *        eth0
192.168.1.77     0x1         0x0         00:00:00:00:00:00     *        eth0
"""


def test_parses_windows_output_and_skips_broadcast_and_multicast() -> None:
    assert parse_arp_output(WINDOWS) == [
        DiscoveredDevice(mac="a4:2b:b0:12:34:56", ip="192.168.1.1"),
        DiscoveredDevice(mac="3c:22:fb:aa:bb:cc", ip="192.168.1.23"),
    ]


def test_parses_macos_output_and_zero_pads_short_octets() -> None:
    assert parse_arp_output(MACOS) == [
        DiscoveredDevice(mac="a4:2b:b0:12:34:56", ip="192.168.1.1"),
        DiscoveredDevice(mac="00:1b:63:0a:0b:0c", ip="192.168.1.40"),
    ]


def test_parses_proc_net_arp_and_skips_incomplete_entries() -> None:
    assert parse_arp_output(PROC_NET_ARP) == [
        DiscoveredDevice(mac="a4:2b:b0:12:34:56", ip="192.168.1.1"),
    ]


def test_same_mac_on_two_interfaces_is_reported_once() -> None:
    text = "10.0.0.1  aa-bb-cc-dd-ee-f0  dynamic\n10.0.1.1  aa-bb-cc-dd-ee-f0  dynamic\n"
    assert len(parse_arp_output(text)) == 1
