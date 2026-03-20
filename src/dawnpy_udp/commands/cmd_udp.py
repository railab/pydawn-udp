# tools/dawnpy/src/dawnpy/commands/cmd_udp.py
#
# SPDX-License-Identifier: Apache-2.0
#

"""Module containing UDP command."""

import click
from dawnpy.cli.environment import Environment, pass_environment
from dawnpy.cli.options import configure_cli_logging

from dawnpy_udp.client import run_console

###############################################################################
# Command: cmd_udp
###############################################################################


@click.command(name="udp")
@click.argument("host", type=str, required=True)
@click.option("--port", "-p", type=int, default=50000, help="UDP port")
@click.option(
    "--descriptor",
    "-d",
    "descriptor_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
    help=(
        "Optional descriptor.yaml path or config directory. When provided, "
        "the console uses descriptor-backed IOs instead of CMD_LIST_IOS "
        "discovery."
    ),
)
@click.option(
    "--debug/--no-debug",
    default=False,
    is_flag=True,
    envvar="DAWNPY_DEBUG",
)
@pass_environment
def cmd_udp(
    ctx: Environment,
    host: str,
    port: int,
    descriptor_path: str | None,
    debug: bool,
) -> bool:
    """Run UDP console for interactive device communication."""
    ctx.debug = debug
    configure_cli_logging(debug)

    # Run the UDP console
    run_console(
        host=host,
        port=port,
        debug=ctx.debug,
        descriptor_path=descriptor_path,
    )

    return True
