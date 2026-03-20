#!/usr/bin/env python3
# tools/dawnpy/src/dawnpy/udp/udp.py
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Simple Python library for communicating with Dawn UDP Protocol devices.

This library implements the Dawn UDP Simple Protocol (CProtoUdp)
for reading/writing IO data and device information.
"""

import socket
import struct
from typing import Any

from dawnpy.objectid import ObjectIdDecoder
from dawnpy.simple_protocol import SimpleProtocolBase


class DawnUdpProtocol(SimpleProtocolBase):  # pragma: no cover
    """Client for communicating with Dawn devices via UDP."""

    def __init__(
        self,
        host: str,
        port: int = 50000,
        timeout: float = 1.0,
        verbose: bool = False,
    ):
        """
        Initialize UDP connection.

        Args:
            host: Target host address (e.g. '127.0.0.1')
            port: Target UDP port
            timeout: Socket timeout in seconds
            verbose: Enable verbose logging
        """
        super().__init__(verbose=verbose)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None

    def _create_objid_decoder(self) -> ObjectIdDecoder | None:
        """Create the object ID decoder for the UDP protocol."""
        return ObjectIdDecoder()

    def connect(self) -> bool:
        """Create UDP socket."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(self.timeout)
            self._log(f"UDP socket created for {self.host}:{self.port}")
            return True
        except OSError as e:
            self._err(f"Failed to create UDP socket: {e}")
            return False

    def disconnect(self) -> None:
        """Close UDP socket."""
        if self.sock:
            self.sock.close()
            self.sock = None
            self._log("UDP socket closed")

    def send_frame(self, cmd: int, payload: bytes = b"") -> bool:
        """Send a frame to the device via UDP."""
        if not self.sock:
            self._err("UDP socket not initialized")
            return False

        if len(payload) > self.FRAME_MAX_PAYLOAD:
            self._err(f"Payload too large: {len(payload)}")
            return False

        frame, _ = self._build_frame(cmd, payload)

        # Send frame
        try:
            self.sock.sendto(frame, (self.host, self.port))
            self._log(f"Sent UDP frame: CMD=0x{cmd:02X} LEN={len(payload)}")
            return True
        except OSError as e:
            self._err(f"Failed to send UDP frame: {e}")
            return False

    def receive_frame(self) -> tuple[int, bytes] | None:
        """Receive a frame from the device via UDP."""
        if not self.sock:
            return None

        try:
            data, addr = self.sock.recvfrom(
                self.FRAME_MAX_PAYLOAD + self.FRAME_MIN_LEN
            )
        except TimeoutError:
            self._err("Timeout waiting for UDP response")
            return None
        except OSError as e:
            self._err(f"UDP receive error: {e}")
            return None

        return self._parse_frame_bytes(
            data,
            short_frame_message="Received short UDP packet ({length} bytes)",
            invalid_sync_message="Invalid sync byte: 0x{sync:02X}",
            length_mismatch_message=(
                "UDP packet length mismatch: expected {expected}, got {actual}"
            ),
            log_message_factory=lambda length: (
                f"Received UDP frame: CMD=0x{data[3]:02X} "
                f"LEN={length} from {addr}"
            ),
        )

    def ping(self) -> bool:
        """Send a ping and wait for a pong response."""
        return self._ping_with_messages(
            start_message="\nPinging device via UDP...",
            success_message="Device responded with PONG via UDP!",
            failure_message="No PONG response from device",
        )

    def get_io_list(self) -> list[int]:
        """Fetch and cache the list of available IO object IDs."""
        self._log("\nGetting available IO objects via UDP...")
        if not self.send_frame(self.CMD_LIST_IOS):
            return []

        frame_data = self.receive_frame()
        if not frame_data:
            return []

        cmd, payload = frame_data
        if cmd != self.CMD_LIST_IOS or len(payload) < 2:
            return []

        return self._parse_io_list_payload(payload)

    def get_io_info(self, objid: int) -> dict[str, Any] | None:
        """Fetch metadata for one IO object."""
        payload = struct.pack("<I", objid)
        if not self.send_frame(self.CMD_GET_INFO, payload):
            return None

        frame_data = self.receive_frame()
        if not frame_data:
            return None

        cmd, response = frame_data
        if cmd != self.CMD_GET_INFO or len(response) < 3:
            return None

        return self._build_io_info(objid, response)

    def read_io(self, objid: int) -> bytes | None:
        """Read raw payload bytes for an IO object."""
        frame = self._exchange_objid(self.CMD_GET_IO, objid)
        cmd, data = frame or (None, None)
        if cmd != self.CMD_GET_IO:
            return None
        return data

    def write_io(self, objid: int, data: bytes) -> bool:
        """Write raw payload bytes to an IO object."""
        frame_data = self._exchange_write(self.CMD_SET_IO, objid, data)
        if not frame_data:
            return False

        cmd, response = frame_data
        return (
            cmd == self.CMD_SET_IO
            and len(response) >= 1
            and response[0] == self.STATUS_OK
        )

    def discover_all_ios(self) -> dict[int, dict[str, Any]]:
        """Read and return metadata (and readable values) for all IOs."""
        if not self.get_io_list():
            return {}

        return self._collect_io_snapshot(
            set_none_for_write_only=False,
            set_none_for_failed_read=False,
        )

    def read_io_seek_chunk(
        self, objid: int, offset: int
    ) -> tuple[int, bytes] | None:
        """Read one chunk from a seekable IO, returning total size and data."""
        payload = struct.pack("<II", objid, offset)
        if not self.send_frame(self.CMD_GET_IO_SEEK, payload):
            return None
        frame_data = self.receive_frame()
        if (
            not frame_data
            or frame_data[0] != self.CMD_GET_IO_SEEK
            or len(frame_data[1]) < 8
        ):
            return None
        response = frame_data[1]
        total_size = struct.unpack("<I", response[4:8])[0]
        return total_size, bytes(response[8:])

    def read_io_seek(self, objid: int) -> bytes | None:
        """Read an entire seekable IO by fetching chunks until complete."""
        return self._read_io_seek_all(objid)
