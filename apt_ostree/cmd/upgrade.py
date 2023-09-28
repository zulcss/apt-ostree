"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd import pass_state_context
from apt_ostree.packages import Packages


@click.command(
    help="Upgrade Debian packages.")
@pass_state_context
def upgrade(state):
    try:
        Packages(state).upgrade()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
