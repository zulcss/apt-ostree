"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import feed_option
from apt_ostree.cmd.options import packages_option
from apt_ostree.cmd.options import release_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.repo import Repo


@click.command(help="Remove debian package(s) from reposiotry.")
@pass_state_context
@feed_option
@release_option
@packages_option
def remove(state, feed, release, packages):
    try:
        Repo(state).remove()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
