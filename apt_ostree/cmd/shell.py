"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging

import click

from apt_ostree.cmd.compose import compose
from apt_ostree.cmd.deploy import deploy
from apt_ostree.cmd.install import install
from apt_ostree.cmd.options import debug_option
from apt_ostree.cmd.options import workspace_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.cmd.remotes import remote
from apt_ostree.cmd.repo import repo
from apt_ostree.cmd.status import status
from apt_ostree.cmd.uninstall import uninstall
from apt_ostree.cmd.upgrade import upgrade
from apt_ostree.cmd.version import version
from apt_ostree.log import setup_log


@click.group(
    help="\nHyrbid image/package management system."
)
@pass_state_context
@debug_option
@workspace_option
def cli(state, debug, workspace):
    setup_log()

    if state.debug:
        click.secho("Running apt-ostree.")
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(f"Creating workspace: {workspace}")
    state.workspace.mkdir(parents=True, exist_ok=True)


def main():
    cli(prog_name="apt-ostree")


cli.add_command(compose)
cli.add_command(deploy)
cli.add_command(install)
cli.add_command(remote)
cli.add_command(repo)
cli.add_command(status)
cli.add_command(uninstall)
cli.add_command(upgrade)
cli.add_command(version)
