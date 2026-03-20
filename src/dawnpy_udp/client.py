#!/usr/bin/env python3
# tools/dawnpy/src/dawnpy/udp/client.py
#
# SPDX-License-Identifier: Apache-2.0
#

"""
UDP console interface for DawnUdpProtocol client.

Provides interactive console for UDP device communication.
"""

import time

from dawnpy.cli.simple_device_client import SimpleDeviceClient
from dawnpy.cli.simple_device_console import SimpleDeviceConsole
from dawnpy.device.decode import decode_value

from dawnpy_udp.udp import DawnUdpProtocol


class UdpClient(SimpleDeviceClient):  # pragma: no cover
    """UDP communication client for Dawn devices."""

    connect_error = "ERROR: Failed to initialize UDP socket"
    ping_error = "ERROR: Failed to ping device via UDP"

    def __init__(
        self,
        host: str,
        port: int = 50000,
        debug: bool = False,
        descriptor_path: str | None = None,
    ) -> None:
        """
        Initialize UDP client.

        Args:
            host: Target host
            port: Target port
        """
        super().__init__(descriptor_path=descriptor_path)
        self.host = host
        self.port = port
        self.debug = debug
        self.client = DawnUdpProtocol(host, port, verbose=debug)

    def discovery(self) -> None:
        """Discover IOs and print a short summary table."""
        if not self.connected:
            print("ERROR: Not connected to device")
            return

        print("=" * 60)
        print("UDP Device Discovery: Basic IO Information")
        print("=" * 60)

        io_data = self.discover_ios()
        self.discovered_ios = io_data

        if not io_data:
            print("No IO objects found")
            return

        for objid, info in io_data.items():
            decoded = self.client.decode_object_id(objid)
            print(f"\nObject ID: 0x{objid:08X} ({decoded})")
            print(f"  Type: {info['io_type_str']}")
            print(f"  Dimension: {info['dimension']}")
            print(f"  Data Type: {info['dtype']}")
            if info.get("data"):
                print(f"  Data (hex): {info['data']}")

    def list_discovered_features(self) -> None:
        """Print details for cached discovery results."""
        if not self.discovered_ios:
            print("No discovered IOs. Run discovery (d) first.")
            return

        print("\nDetailed IO Information:")
        for objid in sorted(self.discovered_ios):
            info = self.discovered_ios[objid]
            decoded = self.client.decode_object_id(objid)
            print(f"\nObject ID: 0x{objid:08X} ({decoded})")
            print(f"  Type: {info.get('io_type_str', 'unknown')}")
            print(f"  Data Type: {info.get('dtype', 'unknown')}")
            if info.get("data") is not None:
                print(f"  Data (hex): {info.get('data')}")

    def monitoring(
        self,
        poll_interval: float = 1.0,
        duration: float = 10.0,
        objids: list[int] | None = None,
    ) -> None:
        """Continuously poll and print values for selected IOs."""
        print("\n" + "=" * 60)
        print("Continuous UDP IO Monitoring")
        print("=" * 60)

        client = DawnUdpProtocol(self.host, self.port)
        try:
            if not client.connect() or not client.ping():
                return
            io_list = objids if objids else self.known_objids()
            if not io_list:
                io_list = client.get_io_list()
            if not io_list:
                print("No IO objects found")
                return

            print(
                f"\nMonitoring {len(io_list)} IO objects for {duration}s...\n"
            )
            start_time = time.time()
            poll_count = 0

            while time.time() - start_time < duration:
                print(f"--- Poll #{poll_count} ---")
                for objid in io_list:
                    data = client.read_io(objid)
                    if data is not None:
                        info = client.get_io_info(objid)
                        dtype = info["dtype"] if info else 0
                        lines = decode_value(
                            data, dtype, client.objid_decoder, objid=objid
                        )
                        for line in lines:
                            print(f"  {line}")
                    else:
                        print(f"  0x{objid:08X}: ERROR")
                poll_count += 1
                time.sleep(poll_interval)
        finally:
            client.disconnect()


class UdpConsole(SimpleDeviceConsole):  # pragma: no cover
    """Interactive UDP console for device communication."""

    def __init__(
        self,
        host: str,
        port: int = 50000,
        debug: bool = False,
        descriptor_path: str | None = None,
    ) -> None:
        """Initialize console state and UDP client."""
        super().__init__(
            prompt="\nEnter UDP command (h for help): ",
            history_file=".dawnpy_udp_history",
        )
        self.client = UdpClient(
            host,
            port,
            debug=debug,
            descriptor_path=descriptor_path,
        )

    def _console_header(self) -> str:
        """Return the UDP startup banner."""
        return f"\nUDP Console - Host: {self.client.host}:{self.client.port}"

    def show_menu(self) -> None:
        """Display available console commands."""
        self.print_menu(
            "UDP Console - Commands",
            [
                "d: Device discovery",
                "l: List discovered features",
                "m [objids]: Continuous monitoring",
                "r <objids>: Read object ID(s)",
                "s <objid>: Read seekable IO",
                "w <objid> <value>: Write value",
                "h: Show help",
                "q: Quit",
            ],
        )


def run_console(  # pragma: no cover
    host: str,
    port: int = 50000,
    debug: bool = False,
    descriptor_path: str | None = None,
) -> None:
    """Run the interactive UDP console."""
    console = UdpConsole(
        host,
        port,
        debug=debug,
        descriptor_path=descriptor_path,
    )
    console.run()
