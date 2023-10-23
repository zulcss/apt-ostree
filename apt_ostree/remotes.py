"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging

from rich.console import Console
from rich.table import Table

from apt_ostree.ostree import Ostree


class Remotes:
    def __init__(self, state):
        self.console = Console()
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.ostree = Ostree(self.state)

    def remotes(self, refs):
        """Dispaly remotes or refs at remotes."""
        if refs:
            self.remote_refs()
        else:
            self.remote_list()

    def remote_refs(self):
        """List all branches associated with a host."""
        refs = self.ostree.remote_refs(self.state.remote)
        if len(refs) == 0:
            return

        table = Table(box=None)
        table.add_column("Remote", justify="center")
        table.add_column("Checksum", justify="center")

        url = self.ostree.get_remote_url(self.state.remote)
        self.logging.info(
            f"\nRemote: {self.state.remote} ({url})\n")
        for remote, csum in refs.items():
            table.add_row(remote, csum)

        if table.columns:
            self.console.print(table)
            self.console.print("\n")

    def remote_list(self):
        """Display the registered hosts."""
        remotes = self._remote_list()
        if len(remotes) == 0:
            return

        table = Table(box=None)
        table.add_column("Remote")
        table.add_column("URL")

        for r in remotes:
            url = self.ostree.get_remote_url(r)
            table.add_row(r, url)

        if table.columns:
            self.console.print(table)

    def remote_add(self):
        """Add remote with a given URL."""
        self.ostree.remote_add()

    def remote_remove(self):
        """Remove remote with a given URL."""
        self.ostree.remote_remove()

    def _remote_list(self):
        """List all remotes but exclude the origin."""
        try:
            return [r for r in self.ostree.remotes_list() if r != "origin"]
        except Exception:
            return []
