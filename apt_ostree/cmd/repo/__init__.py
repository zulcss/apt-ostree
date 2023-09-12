"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import click

from apt_ostree.cmd.repo.add import add
from apt_ostree.cmd.repo.init import init
from apt_ostree.cmd.repo.list import show
from apt_ostree.cmd.repo.remove import remove


@click.group(help="Create/manage Debian package repository.")
@click.pass_context
def repo(ctxt):
    pass


repo.add_command(add)
repo.add_command(init)
repo.add_command(remove)
repo.add_command(show)
