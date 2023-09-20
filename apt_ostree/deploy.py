"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import os
import shutil

from rich.console import Console

from apt_ostree.ostree import Ostree
from apt_ostree import utils


class Deploy:
    def __init__(self, state):
        self.state = state
        self.ostree = Ostree(self.state)
        self.console = Console()

        self.workspace = self.state.workspace
        self.workdir = self.state.workspace.joinpath("deployment")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.rootfs = None

    def prestaging(self, rootfs):
        """Prestage steps."""
        with self.console.status("Running prestaging steps."):
            # Ensure the directory is root:root.
            os.chown(rootfs.joinpath("usr/etc"), 0, 0)
            utils.run_sandbox_command(
                ["systemd-tmpfiles", "--create"], rootfs
            )

    def poststaging(self, rootfs):
        """Post staging steps."""
        self.console.print("Running post deploy steps.")
        os.chown(rootfs.joinpath("usr/etc"), 0, 0)
        # /var is stateless so remove everything that
        # might be lying around.
        shutil.rmtree(rootfs.joinpath("var"))
        os.mkdir(rootfs.joinpath("var"), 0o755)

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
