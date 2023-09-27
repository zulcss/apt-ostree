"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_argument
from apt_ostree.cmd import pass_state_context
from apt_ostree.deploy import Deploy


@click.command(help="Deploy a specific commit.")
@pass_state_context
@branch_argument
@click.option(
    "--update",
    help="Update grub configuration.",
    is_flag=True,
    default=False
)
@click.option(
    "-r", "--reboot",
    help="Initiate a reboot after operation is complete.",
    is_flag=True,
    default=False
)
def deploy(state, branch, update, reboot):
    try:
        Deploy(state).deploy(update, reboot)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
