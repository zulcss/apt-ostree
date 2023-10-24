"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import os
import sys

import click
from rich.console import Console
import yaml

from apt_ostree import utils


class RunCommand:
    def __init__(self, state):
        self.state = state
        self.console = Console()

    def run_command(self, command, mount_points, pre_exec, rootfs):
        """Run a command in an ostree branch."""
        if not os.path.exists(rootfs):
            click.secho(f"Directory not found: {rootfs}", fg="red")
            sys.exit(1)

        mounts = None
        if mount_points:
            self.console.print("Loading configuration.")
            with open(mount_points, "r") as f:
                mounts = yaml.safe_load(f)

        if pre_exec:
            self.console.print(f"Executing pre-command: {pre_exec}",
                               highlight=False)
            cmd = ["systemd-nspawn", "-q", "-D", rootfs]
            cmd += pre_exec.split()
            r = utils.run_command(cmd)
            if r.returncode != 0:
                self.console.print("Sucesfully executed pre-command")

        # Run the systemd-nspawn command.
        cmd = ["systemd-nspawn", "-q"]
        if mounts:
            for m in mounts:
                cmd += (["--bind", f"{m}"])
        cmd += ["-D", rootfs]
        if len(command) != 0:
            cmd += command.split()

        utils.run_command(cmd, check=False)
