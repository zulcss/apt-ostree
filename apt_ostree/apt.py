"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging
import os
import subprocess
import sys

import apt

from apt_ostree.utils import run_sandbox_command


class Apt:
    def __init__(self, state):
        self.logging = logging.getLevelName(__name__)
        self.state = state

    def cache(self, rootfs):
        try:
            cache = apt.Cache(rootdir=rootfs)
        except AttributeError as e:
            self.logging.error(f"Failed to load apt cache: {e.message}")
            sys.exit(1)
        return cache

    def apt_package(self, cache, package):
        """Query the package cache."""
        return cache[package]

    def apt_update(self, rootfs):
        """Run apt-get update."""
        self.logging.info("Running apt-update")
        r = run_sandbox_command(
            ["apt-get", "update", "-y"],
            rootfs,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if r.returncode != 0:
            self.logging.error("Failed to run apt-get update.")
        return r

    def apt_install(self, cache, packages, rootfs):
        """Run apt-get install."""
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        for package in packages:
            version = self.get_version(cache, package)
            pkg = self.apt_package(cache, package)
            if not pkg.is_installed:
                self.logging.info(f"Installing {package} ({version}).")
            else:
                self.logging.info(
                    f"Skipping {package} ({version}), already installed.")
            cmd = ["apt-get", "-y", "install", package]
            r = run_sandbox_command(cmd, rootfs, env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if r.returncode != 0:
                self.logging.error("Failed to run apt-get install")
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
            self.logging.error("Failed to run apt-get upgrade.")
        return r

    def apt_uninstall(self, packages, rootfs):
        """Run apt-get remove."""
        cmd = ["apt-get", "remove"]
        if packages:
            cmd += packages
        r = run_sandbox_command(cmd, rootfs)
        if r.returncode != 0:
            self.logging.error("Failed to run apt-get remove.")
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

    def get_installed_packages(self, cache):
        """Get a list of installed packages."""
        pkgs = set()
        for pkg in cache:
            if pkg.is_installed:
                pkgs.add(pkg.name)
        return pkgs

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
