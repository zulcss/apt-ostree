"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import hashlib
import os
import shutil
import sys

import apt
import click

from apt_ostree.constants import excluded_packages
from apt_ostree.log import complete_step
from apt_ostree.log import log_step
from apt_ostree.ostree import Ostree
from apt_ostree.utils import run_command


class Bootstrap:
    def __init__(self, state):
        self.state = state
        self.ostree = Ostree(self.state)

    def create_rootfs(self):
        """Create a Debian system from a configuration file."""
        if not self.state.repo.exists():
            click.secho(f"Creating ostree repository: {self.state.repo}")
            run_command(["ostree", "init", f"--repo={self.state.repo}",
                         "--mode=archive-z2"])
        else:
            click.secho(f"Found ostree repository: {self.state.repo}")

        click.secho(f"Found ostree branch: {self.state.branch}")

        if not self.state.base.exists():
            click.secho("Configuration directory does not exist.", fg="red")
            sys.exit(1)
        click.secho(f"Found configuration directory: {self.state.base}")

        config = self.state.base.joinpath("bootstrap.yaml")
        if not config.exists():
            click.sceho("bootstrap.yaml does not exist.", fg="red")
            sys.exit(1)
        else:
            click.secho("Found configuration file bootstrap.yaml.")

        with complete_step(f"Setting up workspace for {self.state.branch}."):
            workspace = self.state.workspace
            workdir = workspace.joinpath(f"build/{self.state.branch}")
            rootfs = workdir.joinpath("rootfs")

            log_step(f"Building workspace for {self.state.branch} "
                     f"in {workspace}")
            if workdir.exists():
                log_step("Found working directory from "
                         "previous run...removing.")
                shutil.rmtree(workdir)
            workdir.mkdir(parents=True, exist_ok=True)
            rootfs.mkdir(parents=True, exist_ok=True)

            log_step("Running bdebstrap, please wait.")
            verbosity = "-q"
            if self.state.debug:
                verbosity = "-v"
            run_command(
                ["bdebstrap", "-c", "bootstrap.yaml", verbosity,
                 "--force", "--name", str(
                     self.state.branch), "--target", str(rootfs),
                 "--output", str(workdir)], cwd=self.state.base)

        self.create_ostree(rootfs)
        r = self.ostree.ostree_commit(
            rootfs,
            branch=self.state.branch,
            repo=self.state.repo,
            subject="Commit by apt-ostree",
            msg="Initialized by apt-ostree.")
        if r.returncode != 0:
            click.secho(f"Failed to commit {self.state.branch} to "
                        f"{self.state.repo}.")
        click.secho(f"Commited {self.state.repo} to {self.state.repo}.")

    def create_ostree(self, rootdir):
        """Create an ostree branch from a rootfs."""
        with complete_step(f"Creating ostree from {rootdir}."):
            log_step("Setting up /usr/lib/ostree-boot")
            self.setup_boot(rootdir,
                            rootdir.joinpath("boot"),
                            rootdir.joinpath("usr/lib/ostree-boot"))
            self.create_tmpfile_dir(rootdir)
            self.convert_to_ostree(rootdir)

    def convert_to_ostree(self, rootdir):
        """Convert rootfs to ostree."""
        CRUFT = ["boot/initrd.img", "boot/vmlinuz",
                 "initrd.img", "initrd.img.old",
                 "vmlinuz", "vmlinuz.old"]
        assert rootdir is not None and rootdir != ""

        with complete_step(f"Converting {rootdir} to ostree."):
            dir_perm = 0o755

            # Emptying /dev
            log_step("Emptying /dev.")
            shutil.rmtree(rootdir.joinpath("dev"))
            os.mkdir(rootdir.joinpath("dev"), dir_perm)

            # Copying /var
            self.sanitize_usr_symlinks(rootdir)
            log_step("Moving /var to /usr/rootdirs.")
            os.mkdir(rootdir.joinpath("usr/rootdirs"), dir_perm)
            # Make sure we preserve file permissions otherwise
            # bubblewrap will complain that a file/directory
            # permisisons/onership is not mapped correctly.
            shutil.copytree(
                rootdir.joinpath("var"),
                rootdir.joinpath("usr/rootdirs/var"),
                symlinks=True
            )
            shutil.rmtree(rootdir.joinpath("var"))
            os.mkdir(rootdir.joinpath("var"), dir_perm)

            # Remove unecessary files
            log_step("Removing unnecessary files.")
            for c in CRUFT:
                try:
                    os.remove(rootdir.joinpath(c))
                except OSError:
                    pass

            # Setup and split out etc
            log_step("Moving /etc to /usr/etc.")
            shutil.move(rootdir.joinpath("etc"),
                        rootdir.joinpath("usr"))

            log_step("Setting up /ostree and /sysroot.")
            try:
                rootdir.joinpath("ostree").mkdir(
                    parents=True, exist_ok=True)
                rootdir.joinpath("sysroot").mkdir(
                    parents=True, exist_ok=True)
            except OSError:
                pass

            log_step("Setting up symlinks.")
            TOPLEVEL_LINKS = {
                "media": "run/media",
                "mnt": "var/mnt",
                "opt": "var/opt",
                "ostree": "sysroot/ostree",
                "root": "var/roothome",
                "srv": "var/srv",
                "usr/local": "../var/usrlocal",
            }
            fd = os.open(rootdir, os.O_DIRECTORY)
            for l, t in TOPLEVEL_LINKS.items():
                shutil.rmtree(rootdir.joinpath(l))
                os.symlink(t, l, dir_fd=fd)

    def sanitize_usr_symlinks(self, rootdir):
        """Replace symlinks from /usr pointing to /var"""
        usrdir = os.path.join(rootdir, "usr")
        for base, dirs, files in os.walk(usrdir):
            for name in files:
                p = os.path.join(base, name)

                if not os.path.islink(p):
                    continue

                # Resolve symlink relative to root
                link = os.readlink(p)
                if os.path.isabs(link):
                    target = os.path.join(rootdir, link[1:])
                else:
                    target = os.path.join(base, link)

                rel = os.path.relpath(target, rootdir)
                # Keep symlinks if they're pointing to a location under /usr
                if os.path.commonpath([target, usrdir]) == usrdir:
                    continue

                toplevel = self.get_toplevel(rel)
                # Sanitize links going into /var, potentially
                # other location can be added later
                if toplevel != 'var':
                    continue

                os.remove(p)
                os.link(target, p)

    def get_toplevel(self, path):
        """Get the top level diretory."""
        head, tail = os.path.split(path)
        while head != '/' and head != '':
            head, tail = os.path.split(head)

        return tail

    def setup_boot(self, rootdir, bootdir, targetdir):
        """Setup up the ostree bootdir"""
        vmlinuz = None
        initrd = None
        dtbs = None
        version = None

        try:
            os.mkdir(targetdir)
        except OSError:
            pass

        for item in os.listdir(bootdir):
            if item.startswith("vmlinuz"):
                assert vmlinuz is None
                vmlinuz = item
                _, version = item.split("-", 1)
            elif item.startswith("initrd.img") or item.startswith("initramfs"):
                assert initrd is None
                initrd = item
            elif item.startswith("dtbs"):
                assert dtbs is None
                dtbs = os.path.join(bootdir, item)
            else:
                # Move all other artifacts as is
                shutil.move(os.path.join(bootdir, item), targetdir)
        assert vmlinuz is not None

        m = hashlib.sha256()
        m.update(open(os.path.join(bootdir, vmlinuz), mode="rb").read())
        if initrd is not None:
            m.update(open(os.path.join(bootdir, initrd), "rb").read())

        csum = m.hexdigest()

        os.rename(os.path.join(bootdir, vmlinuz),
                  os.path.join(targetdir, vmlinuz + "-" + csum))

        if initrd is not None:
            os.rename(os.path.join(bootdir, initrd),
                      os.path.join(targetdir,
                                   initrd.replace(
                                       "initrd.img", "initramfs")
                                   + "-" + csum))

    def create_tmpfile_dir(self, rootdir):
        """Ensure directoeies in /var are created."""
        with complete_step("Creating systemd-tmpfiles configuration"):
            cache = apt.cache.Cache(rootdir=rootdir)
            dirs = []
            for pkg in cache:
                if "/var" in pkg.installed_files and \
                        pkg.name not in excluded_packages:
                    dirs += [file for file in pkg.installed_files
                             if file.startswith("/var")]
            if len(dirs) == 0:
                return
            conf = rootdir.joinpath(
                "usr/lib/tmpfiles.d/ostree-integration-autovar.conf")
            if conf.exists():
                os.unlink(conf)
            with open(conf, "w") as f:
                f.write("# Auto-genernated by apt-ostree\n")
                for d in (dirs):
                    if d not in [
                            "/var",
                            "/var/lock",
                            "/var/cache",
                            "/var/spool",
                            "/var/log",
                            "/var/lib"]:
                        f.write(f"L {d} - - - - ../../usr/rootdirs{d}\n")
