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
        if not rootfs.exists():
            click.secho("Unable to determine rootfs: {rootfs}", fg="red")
            sys.exit(1)

        # Step 0 - Setup prestaging.
        self.deploy.prestaging(rootfs)

        # Step 1 - Update the package cache.
        self.apt.apt_update(rootfs)
        cache = self.apt.cache(rootfs)

        # Step 2 - Check for updates.
        self.console.print(
            "Checking for upgradable packages."
        )
        # Fake upgrading so we can determine the packages
        # that need to be upgraded. This is done so we
        # can check for any updates before doing anything
        # else.
        cache.upgrade(False)
        packages = [package.name for package in cache.get_changes()]
        if len(packages) == 0:
            click.secho("No package to upgrade.", fg="red")
            sys.exit(1)

        # Step 3 - Build the commit message
        r = self.apt.apt_list(rootfs, "--upgradable")
        commit = "Packages upgraded: \n\n"
        for line in r.stdout.splitlines():
            line = line.decode("utf-8").strip()
            if line != "Listing...":
                columns = line.split(" ")

                name, repo = columns[0].split("/")
                current = columns[5][:-1]
                update = columns[1]

                commit += f"- {name} ({current} -> {update})\n"

        # Step 4 - Do the upgrade.
        self.apt.apt_upgrade(rootfs)

        # Step 5 - Poststaging.
        self.deploy.poststaging(rootfs)

        # Step 6 - Commit to the repo
        self.console.print(
            f"Commiting to {self.ostree.get_branch()}. Please wait",
            highlight=False)
        self.ostree.ostree_commit(
            root=str(rootfs),
            branch=self.ostree.get_branch(),
            repo=self.state.repo,
            subject="Package Upgrade",
            msg=commit,
        )

        # Step 7 - Cleanup
        self.deploy.cleanup(rootfs)

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
