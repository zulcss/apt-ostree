"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import sys

import click
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
        deps = set()
        predeps = set()
        all_deps = set()

        branch = self.ostree.get_branch()
        rootfs = self.deploy.get_sysroot()
        if not rootfs.exists():
            click.secho("Unable to determine rootfs: {rootfs}", fg="red")
            sys.exit(1)

        # Step 0 - Run the prestaging steps.
        self.deploy.prestaging(rootfs)

        # Step 1 - Update the package cache in the deployment.
        self.apt.apt_update(rootfs)
        cache = self.apt.cache(rootfs)

        # Step 2 - Check to see if the packages are valid.
        packages = self.apt.check_valid_packages(cache, packages)
        if len(packages) == 0:
            click.secho("No valid packages found.", fg="red")
            sys.exit(1)

        # Step 3 - Generate the commit message.
        commit = "New packages installed: \n\n"
        for pkg in packages:
            version = self.apt.get_version(cache, pkg)
            commit += f"- {pkg} ({version})\n"

        deps = self.apt.get_dependencies(
            cache, packages, deps, predeps, all_deps)
        if len(deps) == 0:
            commit += "\nNo new dependencies found."
        else:
            commit += "\nNew Dependencies: \n\n"
            for dep in deps:
                version = self.apt.get_version(cache, dep)
                commit += f"- {dep} ({version})\n"

        # Step 4 - Install the valid packages.
        self.apt.apt_install(packages, rootfs)

        # Step 5 - Run post staging steps.
        self.deploy.poststaging(rootfs)

        # Step 6 - Ostree commit.
        self.console.print(f"Commiting to {branch}",
                           highlight=False)
        self.ostree.ostree_commit(
            root=str(rootfs),
            branch=self.ostree.get_branch(),
            repo=self.state.repo,
            subject="New packages",
            msg=commit,
        )

        # Step 7 - Cleanup
        self.deploy.cleanup(rootfs)

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
