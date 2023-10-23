"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import disablerepo_option
from apt_ostree.cmd.options import enablerepo_option
from apt_ostree.cmd.options import source_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.compose import Compose


@click.command(
    help="Add/Remove Debian package feed.")
@pass_state_context
@enablerepo_option
@disablerepo_option
@source_option
def apt(state,
        enablerepo,
        disablerepo,
        sources):
    try:
        if enablerepo:
            Compose(state).enablerepo()
        if disablerepo:
            Compose(state).disablerepo()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
