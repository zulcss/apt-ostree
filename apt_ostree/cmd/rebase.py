"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_argument
from apt_ostree.cmd.options import reboot_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.rebase import Rebase


@click.command(
    help="Switch to a new tree.")
@pass_state_context
@reboot_option
@click.option(
    "--update",
    help="Pull objects from ostree repository",
    is_flag=True,
    default=False
)
@branch_argument
def rebase(state, reboot, update, branch):
    try:
        Rebase(state).rebase(update)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
