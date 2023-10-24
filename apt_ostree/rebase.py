"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0
"""

import logging
import sys

from rich.console import Console

from apt_ostree.apt import Apt
from apt_ostree.deploy import Deploy
from apt_ostree.ostree import Ostree


class Rebase:
    def __init__(self, state):
        self.state = state
        self.console = Console()
        self.ostree = Ostree(self.state)
        self.deploy = Deploy(self.state)
        self.apt = Apt(self.state)
        self.logging = logging.getLogger(__name__)

    def rebase(self, update):
        """Switch to another branch."""
        # Verify the branch is formatted correctly.
        try:
            (remote, branch) = self.state.branch.split(":")
        except KeyError:
            self.logging.error(
                "Branch must be in the format of <remote>:<branch>"
            )
            sys.exit(1)

        # Make sure that we have remotes configured.
        if len(self._get_remotes()) == 0:
            self.logging.error("No remotes configured.")
            sys.exit(1)

        if update:
            self.logging.info(f"Pulling {branch} from {remote}.")
            with self.console.status(f"Fetching {branch} from {remote}"):
                self._fetch(remote, branch)
            sys.exit(1)
        else:
            # Get the current deployment, check for
            # a deployed sysroot.
            sysroot = self.ostree.get_sysroot()
            if sysroot is None:
                self.logging.error("Not running ostree.", fg="red")
                sys.exit(1)

            csum = sysroot.get_booted_deployment().get_csum()
            origin = sysroot.get_booted_deployment().get_origin()
            refspec = origin.get_string('origin', 'refspec')
            if refspec is None:
                self.logging.error("Unable to determine branch.", fg="red")
                sys.exit(1)

            self.logging.info(f"Rebasing {refspec} on to {self.state.branch}.")
            self.logging.info(f"Local deployment: {refspec} ({csum[:10]}).")

            # Get a list of manually installed packages.
            # These include packages that were installed after an
            # initial boostrap as well.
            current_packages = self.get_current_packages(refspec, csum)

            # If we didnt fetch the latest repository do it now.
            self.logging.info(f"Pulling {branch} from {remote}.")
            self._fetch(remote, branch)

            # Prepare the new branch for deployment.
            ref = self.ostree.ostree_ref(self.state.branch)
            if ref is None:
                self.logging.error(f"Failed to fetch {self.state.branch}")
                sys.exit(1)

            self.logging.debug(f"Fetched {self.state.branch} ({ref[:10]})")

            # Rebase onto the pristeine branch.
            rootfs = self.deploy.get_sysroot(self.state.branch)
            if rootfs is None:
                self.logging.error(f"Unable to checkout {self.state.branch}")
                sys.exit(1)

            # Prestaging
            self.deploy.prestaging(rootfs)
            self.apt.apt_update(rootfs)
            cache = self.apt.cache(rootfs)
            new_packages = self.apt.get_installed_packages(cache)

            # Determine packages that are missing and install them.
            self.logging.debug(
                f"Determing package delta between {refspec} "
                f"and {self.state.branch}."
            )
            packages = list(current_packages - new_packages)
            if len(packages) != 0:
                commit = f"Resynchronize {self.state.branch} ({ref[:10]})"\
                         f" with {refspec} ({csum[:10]}).\n\n"
                subject = "Resynchronize package list"
                for pkg in packages:
                    version = self.apt.get_version(cache, pkg)
                    commit += f" - {pkg} {version}"
                    self.logging.info(f"Installing {pkg} ({version}).")
                self.apt.apt_install(cache, packages, rootfs)
            else:
                subject = f"Updated {origin}"
                commit = "Previous deployment: {csum[:10]}"

            self.deploy.poststaging(rootfs)

            self.logging.info(f"Commiting to {self.state.branch}.")
            self.ostree.ostree_commit(
                root=str(rootfs),
                branch=self.state.branch,
                repo=self.state.repo,
                subject=subject,
                msg=commit
            )

            self.deploy.cleanup(rootfs)

    def _get_remotes(self):
        """List of remotes configured."""
        return [
            refs for refs in self.ostree.remotes_list()
            if refs != "origin"]

    def _fetch(self, remote, branch):
        """Wrapper around ostree fertch."""
        self.ostree.fetch(remote, branch)

    def get_current_packages(self, branch, ref):
        """Steps to prepare the systeem before a rebase."""
        self.logging.debug(
            f"Deploying current deployment {branch} ({ref[:10]})")
        rootfs = self.deploy.get_sysroot(branch)
        if not rootfs.exists():
            self.logging.error("Unable to determine rootfs: {rootfs}")
            sys.exit(1)

        # Deploy the current booted deployment and run apt-update
        # to configure apt.
        self.deploy.prestaging(rootfs)
        self.apt.apt_update(rootfs)

        # Check for packages that are installed.
        self.logging.debug("Querying installed packages.")
        cache = self.apt.cache(rootfs)
        pkgs = self.apt.get_installed_packages(cache)

        # Just remove the directory since we are done with it
        self.deploy.cleanup(rootfs)

        return pkgs
