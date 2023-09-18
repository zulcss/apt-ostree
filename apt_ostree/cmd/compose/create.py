"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.bootstrap import Bootstrap
from apt_ostree.cmd.options import compose_options
from apt_ostree.cmd import pass_state_context


@click.command(short_help="Create treefile.")
@pass_state_context
@compose_options
def create(state, repo, base, branch):
    try:
        Bootstrap(state).create_rootfs()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("errror - No space left on device.")
