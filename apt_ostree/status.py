"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import pathlib
import shlex

from rich.console import Console
from rich.table import Table

from apt_ostree.ostree import Ostree


class Status:
    def __init__(self, state):
        self.state = state
        self.ostree = Ostree(state)
        self.console = Console()
        self.sysroot = None

    def get_deployment(self):
        """Get information about the current deployment"""
        self.sysroot = self.ostree.get_sysroot()
        deployment = self.sysroot.get_booted_deployment()

        table = Table(box=None)
        table.add_row("Current Deployment:")
        table.add_row()
        table.add_row("Branch:", f"[green]{self.ostree.get_branch()}[/green]")
        table.add_row("Commit:", f"{deployment.get_csum()}")

        root = self._get_deployment_path(deployment)
        os_release = self._get_os_release(root)
        if deployment.get_osname() == "debian":
            release = os_release.get("PRETTY_NAME").replace('"', '')
            table.add_row("Debian Release:", release)

        table.add_row()

        if table.columns:
            self.console.print(table)

    def _get_deployment_path(self, target_deployment):
        """Get the path for the /sysroot"""
        return pathlib.Path("/" + self.sysroot.get_deployment_dirpath(
            target_deployment))

    def _get_os_release(self, rootfs):
        """Parse the /etc/os-release file."""
        try:
            file = open(rootfs.joinpath("/etc/os-release"), encoding="utf-8")
        except FileNotFoundError:
            try:
                file = open(rootfs.joinpath(
                    "/usr/lib/os-release"), encoding="utf-8")
            except FileNotFoundError:
                return {}

        os_release = {}
        for line in file.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                k, v = line.split("=")
                (v_parsed, ) = shlex.split(v)  # expect only one token
            except ValueError:
                continue
            os_release[k] = v
        return os_release
