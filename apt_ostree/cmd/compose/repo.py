"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_option
from apt_ostree.cmd.options import enablerepo_option
from apt_ostree.cmd.options import repo_option
from apt_ostree.cmd.options import source_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.compose import Compose


@click.command(
    help="Manage a Debian package feed in a Ostree branch.")
@pass_state_context
@branch_option
@repo_option
@enablerepo_option
@source_option
def repo(state,
         branch,
         repo,
         enablerepo,
         sources):
    try:
        Compose(state).enablerepo()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("errror - No space left on device.")
