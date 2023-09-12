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

from apt_ostree.log import log_step
from apt_ostree.utils import run_command


class Repo:
    def __init__(self, state):
        self.state = state
        self.repo = self.state.feed
        self.console = Console()

        self.label = "StarlingX project udpates."
        self.arch = "amd64"
        self.description = "Apt repository for StarlingX updates."

    def init(self):
        """Create a Debian archive from scratch."""
        log_step("Creating Debian package archive.")
        self.repo = self.repo.joinpath("conf")
        if not self.repo.exists():
            log_step("Creating package feed directory")
            self.repo.mkdir(parents=True, exist_ok=True)

        config = self.repo.joinpath("distributions")
        if config.exists():
            log_step("Found existing configuration")
            sys.exit(1)
        else:
            log_step("Creating reprepro configuration")
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
            log_step(f"Adding {pkg}")
            r = run_command(
                ["reprepro", "-b", str(self.repo), "includedeb",
                 self.state.release, pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True)
            if r.returncode == 0:
                log_step(f"Successfully added {pkg}\n")
            else:
                log_step(f"Failed to add {pkg}\n")

    def show(self):
        """Display a table of packages in the archive."""
        r = run_command(
            ["reprepro", "-b", str(self.repo), "list", self.state.release],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            )
        if r.returncode != 0:
            click.secho(r.stdout.decode("utf-8"))
        if "Exiting" in r.stdout.decode("utf-8"):
            click.secho(r.stdout.decode("utf-8"))
        else:
            table = Table()
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
            log_step(f"Removing {pkg}")
            r = run_command(
                ["reprepro", "-b", str(self.repo), "remove",
                 self.state.release, pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True)
            if r.returncode == 0:
                log_step(f"Successfully removed {pkg}\n")
            else:
                log_step(f"Failed to remove {pkg}\n")
