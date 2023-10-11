"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import logging
import pathlib
import shutil
import sys


from rich.console import Console

from apt_ostree.ostree import Ostree
from apt_ostree.repo import Repo


class Compose:
    def __init__(self, state):
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.ostree = Ostree(self.state)
        self.repo = Repo(self.state)
        self.console = Console()

        self.workspace = self.state.workspace
        self.workdir = self.state.workspace.joinpath("deployment")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.rootfs = None

    def create(self):
        """Create an OSTree repository."""
        if self.state.repo.exists():
            self.logging.error(
                f"Repository already exists: {self.state.repo}")
            sys.exit(1)

        self.logging.info(f"Found ostree repository: {self.state.repo}")
        self.ostree.init()

    def backup(self, export_dir):
        """Export branch to a new ostree repo."""
        export_dir = pathlib.Path(export_dir)
        if not export_dir.exists():
            self.logging.error("Ostree export repo does not exist")
            sys.exit(1)

        # Copy the existing branch from one repository to another.
        self.console.print(
            f"Pulling from {self.state.branch} to {export_dir}.",
            highlight=False)
        self.ostree.ostree_pull(export_dir)

    def restore(self, import_dir):
        """Import a branch into a repostiory."""
        import_dir = pathlib.Path(import_dir)
        if not import_dir.exists():
            self.logging.error("Ostree export repo does not exist")
            sys.exit(1)

        # Copy the existing branch from one repository to another.
        self.console.print(
            f"Pulling from {self.state.branch} to {import_dir}.",
            highlight=False)
        self.ostree.ostree_pull(import_dir)

    def enablerepo(self):
        """Enable Debian package feed."""
        try:
            self.repo.add_repo()
        except Exception as e:
            self.logging.error(f"Failed to add repo: {e}")
            sys.exit(1)

    def disablerepo(self):
        self.repo.disable_repo()

    def commit(self, parent):
        """Commit changes to an ostree repo."""
        self.logging.info(f"Cloning {self.state.branch} from {parent}.")
        rev = self._checkout(parent)
        if not rev:
            self.logging.error("Failed to fetch commit")
            sys.exit(1)

        with self.console.status(f"Commiting {rev[:10]}."):
            r = self.ostree.ostree_commit(
                root=self.rootfs,
                branch=self.state.branch,
                parent=rev,
                repo=self.state.repo,
                subject="Forked from parent",
                msg=f"Forked from {parent} ({rev[:10]})."
            )
            if r.returncode != 0:
                self.logging.error("Failed to commit.")
                sys.exit(1)

        self.logging.info(f"Successfully commited {self.state.branch}"
                          f"({rev[:10]}) from {parent}.")
        self.logging.info("Cleaning up.")
        try:
            shutil.rmtree(self.rootfs)
        except OSError as e:
            self.logging.error(f"Failed to remove rootfs {self.rootfs}: {e}")

    def _checkout(self, branch):
        """Checkout a commit from an ostree branch."""
        rev = self.ostree.ostree_ref(branch)
        with self.console.status(f"Checking out {rev[:10]}..."):
            self.workdir = self.workdir.joinpath(branch)
            self.workdir.mkdir(parents=True, exist_ok=True)
            self.rootfs = self.workdir.joinpath(rev)
            if self.rootfs.exists():
                shutil.rmtree(self.rootfs)
            self.ostree.ostree_checkout(branch, self.rootfs)
        return rev
