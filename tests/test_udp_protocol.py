#!/usr/bin/env python3
# tools/dawnpy/tests/test_udp_protocol.py
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Unit tests for the Dawn UDP Protocol implementation.
"""

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
