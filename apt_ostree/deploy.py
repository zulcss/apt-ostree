"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging
import os
import shutil
import subprocess
import sys

from rich.console import Console

from apt_ostree.ostree import Ostree
from apt_ostree import utils


class Deploy:
    def __init__(self, state):
        self.console = Console()
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.ostree = Ostree(self.state)

        self.workspace = self.state.workspace
        self.workdir = self.state.workspace.joinpath("deployment")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.rootfs = None

    def prestaging(self, rootfs):
        """Pre stage steps."""
        if not rootfs.exists():
            self.logging.error("rootfs not found: {rootfs}")
            sys.exit(1)

        with self.console.status("Running prestaging steps."):
            fd = os.open(rootfs,  os.O_DIRECTORY)
            # Ensure that we correct permissions
            os.chown(rootfs, 0, 0)
            if not rootfs.joinpath("etc").exists():
                os.symlink("usr/etc", "etc", dir_fd=fd)
                os.chown(rootfs.joinpath("usr/etc"), 0, 0)
            if rootfs.joinpath("usr/rootdirs/var/lib/dpkg").exists():
                # /var is suppose to hold the state of the running
                # system.
                os.rmdir("var", dir_fd=fd)
                os.symlink("usr/rootdirs/var", "var", dir_fd=fd)

                r = utils.run_command(
                    ["systemd-tmpfiles", f"--root={rootfs}", "--create",
                     "--boot", "--prefix=/var"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # According to systemd-tmpfiles(8), the return values are:
                #  0 - success
                # 65 - so some lines had to be ignored, but no other errors
                # 73 - configuration ok, but could not be created
                #  1 - other error
                if r.returncode not in [0, 65]:
                    self.logging.error("Failed to populate /var,")
                    self.logging.error(f"Error code: {r.returncode}")
                    sys.exit(1)

    def poststaging(self, rootfs):
        """Post staging steps."""
        if not rootfs.exists():
            self.logging.error("rootfs not found: {rootfs}")
            sys.exit(1)

        self.logging.info("Running post deploy steps.")
        fd = os.open(rootfs, os.O_DIRECTORY)
        if os.path.exists(rootfs.joinpath("etc")):
            os.unlink("etc", dir_fd=fd)
        os.chown(rootfs.joinpath("usr/etc"), 0, 0)
        if rootfs.joinpath("usr/rootdirs/var/lib/dpkg").exists():
            # /var is stateless so remove everything that
            # might be lying around.
            os.chown(rootfs.joinpath("usr/rootdirs/var"), 0, 0)
            if rootfs.joinpath("var"):
                os.unlink("var", dir_fd=fd)
                os.mkdir("var", dir_fd=fd, mode=0o755)

    def cleanup(self, rootfs):
        """Remove workspace directores to save space."""
        with self.console.status("Cleaning up."):
            shutil.rmtree(rootfs)

    def get_sysroot(self):
        """Checkout the commit to the specified directory."""
        branch = self.ostree.get_branch()
        rev = self.ostree.ostree_ref(branch)
        with self.console.status(f"Checking out {rev[:10]}..."):
            self.workdir = self.workdir.joinpath(branch)
            self.workdir.mkdir(parents=True, exist_ok=True)
            self.rootfs = self.workdir.joinpath(rev)
            if self.rootfs.exists():
                shutil.rmtree(self.rootfs)
            self.ostree.ostree_checkout(branch, self.rootfs)
        return self.rootfs

    def deploy(self, reboot):
        """Run ostree admin deploy."""
        ref = self.ostree.ostree_ref(self.state.branch)
        if not ref:
            self.logging.error(
                f"Unable to find branch: {self.state.branch}.")
            sys.exit(1)

        r = utils.run_command(
            ["ostree", "admin", "deploy", self.state.branch]
        )
        if r.returncode != 0:
            self.logging.error("Failed to deploy.")
            sys.exit(1)

        if reboot:
            self.logging.info("Updating grub.")
            r = utils.run_command(
                ["update-grub"]
            )
            if r.returncode != 0:
                self.logging.error("Failed to update grub.")
                sys.exit(1)

            self.logging.info("Rebooting now.")
            r = utils.run_command(
                ["shutdown", "-r", "now"]
            )
            if r.returncode != 0:
                self.logging.error("Failed to reboot.")
                sys.exit(1)
        else:
            self.logging.info("Please reboot for the changes to take affect.")
