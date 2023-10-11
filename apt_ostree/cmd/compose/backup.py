"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_option
from apt_ostree.cmd.options import repo_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.compose import Compose


@click.command(
    name="export",
    help="Export a branch from an ostree repository.")
@pass_state_context
@repo_option
@branch_option
@click.argument(
    "export_dir"
)
def backup(state, repo, branch, export_dir):
    try:
        Compose(state).backup(export_dir)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
