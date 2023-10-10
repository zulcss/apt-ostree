"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click


from apt_ostree.cmd.options import feed_option
from apt_ostree.cmd.options import origin_option
from apt_ostree.cmd.options import release_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.repo import Repo


@click.command(help="Create a Debian package repsoitory.")
@pass_state_context
@feed_option
@release_option
@origin_option
def init(state, feed, release, origin):
    try:
        Repo(state).init()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
