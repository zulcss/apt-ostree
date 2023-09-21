"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import subprocess
import sys
import textwrap

import click

from rich.console import Console
from rich.table import Table

from apt_ostree.deploy import Deploy
from apt_ostree.log import log_step
from apt_ostree.ostree import Ostree
from apt_ostree import utils


class Repo:
    def __init__(self, state):
        self.state = state
        self.repo = self.state.feed
        self.deploy = Deploy(self.state)
        self.ostree = Ostree(self.state)
        self.console = Console()

        self.label = "StarlingX project udpates."
        self.arch = "amd64"
        self.description = "Apt repository for StarlingX updates."

    def init(self):
        """Create a Debian archive from scratch."""
        log_step("Creating Debian package archive.")
        self.repo = self.repo.joinpath("conf")
        if not self.repo.exists():
            log_step("Creating package feed directory.")
            self.repo.mkdir(parents=True, exist_ok=True)

        config = self.repo.joinpath("distributions")
        if config.exists():
            log_step("Found existing reprepro configuration.")
            sys.exit(1)
        else:
            log_step("Creating reprepro configuration.")
            config.write_text(
                textwrap.dedent(f"""\
                 Origin: {self.state.origin}
                 Label: {self.label}
                 Codename: {self.state.release}
                 Architectures: amd64
                 Components: {self.state.origin}
                 Description: {self.description}
                """)
            )
            options = self.repo.joinpath("options")
            if not options.exists():
                options.write_text(
                    textwrap.dedent(f"""\
                    basedir {self.repo}
                    """)
                )

    def add(self):
        """Add Debian package(s) to repository."""
        for pkg in self.state.packages:
            log_step(f"Adding {pkg}.")
            r = utils.run_command(
                ["reprepro", "-b", str(self.repo), "includedeb",
                 self.state.release, pkg])
            if r.returncode == 0:
                log_step(f"Successfully added {pkg}\n")
            else:
                log_step(f"Failed to add {pkg}\n")

    def show(self):
        """Display a table of packages in the archive."""
        r = utils.run_command(
            ["reprepro", "-b", str(self.repo), "list", self.state.release],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        # Repo not configured yet
        if r.returncode == 254:
            sys.exit(1)
        if r.returncode != 0:
            click.secho(r.stdout.decode("utf-8"))
        if r.stdout and "Exiting" in r.stdout.decode("utf-8"):
            click.secho(r.stdout.decode("utf-8"))
        else:
            table = Table(box=None)
            table.add_column("Package")
            table.add_column("Version")
            table.add_column("Release")
            table.add_column("Origin")
            table.add_column("Architecture")

            for line in r.stdout.decode("utf-8").splitlines():
                (metadata, package, version) = line.split()
                (suite, origin, arch) = metadata.split("|")
                table.add_row(package, version, suite, origin, arch[:-1])

            self.console.print(table)

    def remove(self):
        """Remove a Debian package from an archive."""
        for pkg in self.state.packages:
            log_step(f"Removing {pkg}.")
            r = utils.run_command(
                ["reprepro", "-b", str(self.repo), "remove",
                 self.state.release, pkg],
                check=True)
            if r.returncode == 0:
                log_step(f"Successfully removed {pkg}\n")
            else:
                log_step(f"Failed to remove {pkg}\n")

    def add_repo(self):
        """Enable Debian feed via apt-add-repository."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()
        self.deploy.prestaging(rootfs)
        self.console.print(
            "Enabling addtional Debian package feeds.")
        cmd = [
            "apt-add-repository",
            "-y", "-n",
            self.state.sources
        ]
        r = utils.run_sandbox_command(
            cmd,
            rootfs,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if r.returncode != 0:
            click.secho("Failed to add package feed.", fg="red")
            sys.exit(1)
        self.console.print(
            f"Successfully added \"{self.state.sources}\".", highlight=False)
        self.deploy.poststaging(rootfs)

        self.console.print(f"Committing to {branch} to repo.")
        r = self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Enable package feed.",
            msg=f"Enabled {self.state.sources}",
        )
        if r.returncode != 0:
            click.secho("Failed to commit to repository", fg="red")
        self.deploy.cleanup(str(rootfs))
