#!/usr/bin/env python3
# tools/dawnpy/tests/test_udp_protocol.py
#
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for the Dawn UDP Protocol implementation."""

from unittest.mock import Mock

import pytest

from dawnpy_udp.udp import DawnUdpProtocol


@pytest.fixture
def client():
    """Fixture to create a DawnUdpProtocol client for testing."""
    return DawnUdpProtocol("127.0.0.1", port=50000)


class TestCRCCalculation:
    def test_single_byte(self, client):
        result = client.calculate_crc(b"\x00")
        assert result == 0xE1F0

    def test_multiple_bytes(self, client):
        result = client.calculate_crc(b"\x01\x02\x03")
        assert result == 0xADAD


class TestCommandConstants:
    @pytest.mark.parametrize(
        "cmd_name,expected_value",
        [
            ("CMD_PING", 0x00),
            ("CMD_PONG", 0x01),
            ("CMD_GET_IO", 0x10),
            ("CMD_SET_IO", 0x11),
            ("CMD_GET_INFO", 0x20),
            ("CMD_LIST_IOS", 0x21),
            ("CMD_ERROR", 0xFF),
        ],
    )
    def test_command_constants(self, client, cmd_name, expected_value):
        actual_value = getattr(client, cmd_name)
        assert actual_value == expected_value


class TestPortConfiguration:
    def test_client_settings(self):
        client = DawnUdpProtocol("192.168.1.10", port=12345, timeout=5.0)
        assert client.host == "192.168.1.10"
        assert client.port == 12345
        assert client.timeout == 5.0


def test_udp_initialization():
    client = DawnUdpProtocol("localhost")
    assert client.sock is None
    assert client.io_list == []
    assert client.io_info == {}


def test_ping_retries_once_after_initial_timeout(client):
    client.send_frame = Mock(return_value=True)
    client.receive_frame = Mock(side_effect=[None, (client.CMD_PONG, b"")])

    assert client.ping() is True
    assert client.send_frame.call_count == 2
    assert client.receive_frame.call_count == 2


def test_read_io_retries_once_after_initial_timeout(client):
    client.send_frame = Mock(return_value=True)
    client.receive_frame = Mock(
        side_effect=[None, (client.CMD_GET_IO, b"\x12\x34")]
    )

    assert client.read_io(0x12345678) == b"\x12\x34"
    assert client.send_frame.call_count == 2
    assert client.receive_frame.call_count == 2


def test_write_io_does_not_retry_after_timeout(client):
    client.send_frame = Mock(return_value=True)
    client.receive_frame = Mock(return_value=None)

    assert client.write_io(0x12345678, b"\x01") is False
    assert client.send_frame.call_count == 1
    assert client.receive_frame.call_count == 1
