"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import click

from apt_ostree.cmd.remotes.add import add
from apt_ostree.cmd.remotes.remove import delete
from apt_ostree.cmd.remotes.show import show


@click.group(help="Manage ostree remotes.")
@click.pass_context
def remote(ctxt):
    pass


remote.add_command(add)
remote.add_command(delete)
remote.add_command(show)
