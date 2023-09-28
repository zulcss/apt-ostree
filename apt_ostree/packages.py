"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

from rich.console import Console

from apt_ostree.apt import Apt
from apt_ostree.deploy import Deploy
from apt_ostree.ostree import Ostree


class Packages:
    def __init__(self, state):
        self.state = state
        self.apt = Apt(self.state)
        self.ostree = Ostree(self.state)
        self.console = Console()
        self.deploy = Deploy(self.state)

    def install(self, packages):
        """Use apt to install Debian packages."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()

        self.deploy.prestaging(rootfs)
        self.apt.apt_update(rootfs)
        self.apt.apt_install(packages, rootfs)
        self.deploy.poststaging(rootfs)
        self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Install package",
            msg=f"installed {' '.join(packages)}.",
        )
        self.deploy.cleanup(str(rootfs))

    def upgrade(self):
        """Use apt to install Debian packages."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()

        self.deploy.prestaging(rootfs)
        self.apt.apt_update(rootfs)
        self.apt.apt_upgrade(rootfs)
        self.deploy.poststaging(rootfs)
        self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Upgrade apckages",
            msg="Upgraded packages",
        )
        self.deploy.cleanup(str(rootfs))

    def uninstall(self, packages):
        """Use apt to uninstall Debian packages."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()

        self.deploy.prestaging(rootfs)
        self.apt.apt_uninstall(packages, rootfs)
        self.deploy.poststaging(rootfs)
        self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Uninstall package",
            msg=f"uninstalled {' '.join(packages)}.",
        )
        self.deploy.cleanup(str(rootfs))
