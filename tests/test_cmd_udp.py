"""Tests for dawnpy-udp CLI command wiring."""

from click.testing import CliRunner

import dawnpy_udp.commands.cmd_udp as cmd_udp_mod
from dawnpy_udp.commands.cmd_udp import cmd_udp


def test_udp_console_accepts_descriptor_option(monkeypatch, tmp_path):
    """The console should pass --descriptor through to run_console."""
    descriptor = tmp_path / "descriptor.yaml"
    descriptor.write_text("ios: []\n", encoding="utf-8")
    calls = []

    def _run_console(host, port=50000, debug=False, descriptor_path=None):
        calls.append((host, port, debug, descriptor_path))

    monkeypatch.setattr(cmd_udp_mod, "run_console", _run_console)

    result = CliRunner().invoke(
        cmd_udp,
        [
            "127.0.0.1",
            "--descriptor",
            str(descriptor),
            "--port",
            "50001",
        ],
    )

    assert result.exit_code == 0
    assert calls == [("127.0.0.1", 50001, False, str(descriptor))]


def test_udp_help_documents_descriptor_option():
    """CLI help should expose descriptor-backed discovery."""
    result = CliRunner().invoke(cmd_udp, ["--help"])

    assert result.exit_code == 0
    assert "--descriptor" in result.output
    assert "CMD_LIST_IOS" in result.output
