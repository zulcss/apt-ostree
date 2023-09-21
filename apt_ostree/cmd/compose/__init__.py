"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import click

from apt_ostree.cmd.compose.commit import commit
from apt_ostree.cmd.compose.create import create
from apt_ostree.cmd.compose.image import image
from apt_ostree.cmd.compose.install import install
from apt_ostree.cmd.compose.repo import repo
from apt_ostree.cmd.compose.uninstall import uninstall
from apt_ostree.cmd.compose.upgrade import upgrade


@click.group(help="Commands to build ostree repo/image.")
@click.pass_context
def compose(ctxt):
    pass


compose.add_command(commit)
compose.add_command(create)
compose.add_command(image)
compose.add_command(install)
compose.add_command(upgrade)
compose.add_command(repo)
compose.add_command(uninstall)
