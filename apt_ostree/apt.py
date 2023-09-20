"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import click

from apt_ostree.utils import run_sandbox_command


class Apt:
    def __init__(self, state):
        self.state = state

    def apt_update(self, rootfs):
        """Run apt-get update."""
        r = run_sandbox_command(
            ["apt-get", "update", "-y"],
            rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get update", fg="red")
        return r

    def apt_install(self, packages, rootfs):
        """Run apt-get install."""
        cmd = ["apt-get", "install"]
        if packages:
            cmd += packages
        r = run_sandbox_command(cmd, rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get install", fg="red")
        return r

    def apt_upgrade(self, rootfs):
        """Run apt-get upgrade."""
        r = run_sandbox_command(
            ["apt-get", "upgrade"],
            rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get upgrade", fg="red")
        return r
