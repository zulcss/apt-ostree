"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import remote_option
from apt_ostree.cmd.options import url_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.remotes import Remotes


@click.command(name="add", help="Add a remote repository.")
@pass_state_context
@remote_option
@url_option
def add(state, remote, url):
    try:
        Remotes(state).remote_add()
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
