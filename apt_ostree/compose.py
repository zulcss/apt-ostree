"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import shutil
import sys


import click
from rich.console import Console

from apt_ostree.ostree import Ostree


class Compose:
    def __init__(self, state):
        self.state = state
        self.ostree = Ostree(self.state)
        self.console = Console()

        self.workspace = self.state.workspace
        self.workdir = self.state.workspace.joinpath("deployment")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.rootfs = None

    def commit(self, parent):
        """Commit changes to an ostree repo."""
        self.console.print(f"Cloning {self.state.branch} from {parent}.",
                           highlight=False)
        rev = self._checkout(parent)
        if not rev:
            click.secho("Failed to fetch commit", fg="red")
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
                click.secho("Failed to commit.", fg="red")
                sys.exit(1)

        self.console.print(f"Successfully commited {self.state.branch}"
                           f"({rev[:10]}) from {parent}.",
                           highlight=False)
        self.console.print("Cleaning up.")
        try:
            shutil.rmtree(self.rootfs)
        except OSError as e:
            click.secho(f"Failed to remove rootfs {self.rootfs}: {e}",
                        fg="red")

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
