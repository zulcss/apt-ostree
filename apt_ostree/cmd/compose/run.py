"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd import pass_state_context
from apt_ostree.run import RunCommand


@click.command(
    name="exec",
    help="Run a command or shell from an Ostree branch.")
@pass_state_context
@click.option(
    "--mounts",
    help="Path to yaml configuration for mount points.",
    type=click.Path(exists=True)
)
@click.option(
    "--root",
    help="Path to operate on",
)
@click.option(
    "--pre-exec",
    'pre_exec',
    help="Run the command before executing the container",
)
@click.argument(
    "cmd",
    # If command not specified then execute a shell.
    default=""
)
def run(state,
        mounts,
        root,
        pre_exec,
        cmd):
    try:
        RunCommand(state).run_command(cmd, mounts, pre_exec, root)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
