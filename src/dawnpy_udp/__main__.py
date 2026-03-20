"""Standalone CLI entry point for dawnpy-udp."""

from dawnpy_udp.commands.cmd_udp import cmd_udp


def main() -> None:
    """Run the UDP CLI."""
    cmd_udp(prog_name="dawnpy-udp")


if __name__ == "__main__":
    main()
