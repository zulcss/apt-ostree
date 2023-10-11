"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import subprocess
import sys

import apt
import click
from rich.console import Console

from apt_ostree.utils import run_sandbox_command


class Apt:
    def __init__(self, state):
        self.state = state
        self.console = Console()

    def cache(self, rootfs):
        try:
            cache = apt.Cache(rootdir=rootfs)
        except AttributeError as e:
            click.secho(f"Failed to load apt cache: {e.message}")
            sys.exit(1)
        return cache

    def apt_package(self, cache, package):
        """Query the package cache."""
        return cache[package]

    def apt_update(self, rootfs):
        """Run apt-get update."""
        r = run_sandbox_command(
            ["apt-get", "update", "-y"],
            rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get update", fg="red")
        return r

    def apt_install(self, packages, rootfs):
        """Run apt-get install."""
        cmd = ["apt-get", "install"]
        if packages:
            cmd += packages
        r = run_sandbox_command(cmd, rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get install", fg="red")
        return r

    def apt_list(self, rootfs, action):
        """Show package versions."""
        return run_sandbox_command(
                ["apt", "list", action],
                rootfs,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL)

    def apt_upgrade(self, rootfs):
        """Run apt-get upgrade."""
        r = run_sandbox_command(
            ["apt-get", "upgrade"],
            rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get upgrade", fg="red")
        return r

    def apt_uninstall(self, packages, rootfs):
        """Run apt-get remove."""
        cmd = ["apt-get", "remove"]
        if packages:
            cmd += packages
        r = run_sandbox_command(cmd, rootfs)
        if r.returncode != 0:
            click.secho("Failed to run apt-get remove", fg="red")
        return r

    def check_valid_packages(self, cache, packages):
        """Check for existing non-installed package"""
        pkgs = []
        for package in packages:
            if package in cache:
                pkg = self.apt_package(cache, package)
                if not pkg.is_installed:
                    pkgs.append(package)
        return pkgs

    def get_version(self, cache, package):
        return self.apt_package(cache, package).candidate.version

    def get_dependencies(self, cache, packages, deps, predeps, all_deps):
        """Get installed versions."""
        for pkg in packages:
            deps = self._get_dependencies(
                cache, self.apt_package(cache, pkg), deps, "Depends")
            predeps = self._get_dependencies(
                cache, self.apt_package(cache, pkg), deps, "PreDepends")
        all_deps.update(deps, predeps)
        all_deps = self.check_valid_packages(cache, list(all_deps))
        return all_deps

    def _get_dependencies(self, cache, pkg, deps, key="Depends"):
        """Parse the individual dependencies."""
        candver = cache._depcache.get_candidate_ver(pkg._pkg)
        if candver is None:
            return deps
        dependslist = candver.depends_list
        if key in dependslist:
            for depVerList in dependslist[key]:
                for dep in depVerList:
                    if dep.target_pkg.name in cache:
                        deps.add(dep.target_pkg.name)
        return deps
