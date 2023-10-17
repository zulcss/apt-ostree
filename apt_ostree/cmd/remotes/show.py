"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import remote_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.remotes import Remotes


@click.command(name="list", help="List remotes.")
@pass_state_context
@remote_option
@click.option(
    "--refs",
    help="List remote branches",
    default=False,
    is_flag=True
)
def show(state, remote, refs):
    try:
        Remotes(state).remotes(refs)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
