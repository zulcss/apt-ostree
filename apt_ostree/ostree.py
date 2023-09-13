"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import subprocess
import sys

import click

from apt_ostree.utils import run_command

# pylint: disable=wrong-import-position
import gi
gi.require_version("OSTree", "1.0")
from gi.repository import Gio, GLib, OSTree  # noqa: H301


class Ostree:
    def __init__(self, state):
        self.state = state

    def ostree_commit(self,
                      root=None,
                      repo=None,
                      branch=None,
                      subject=None,
                      msg=None):
        """Commit rootfs to ostree repository."""
        cmd = ["ostree", "commit"]
        if repo:
            cmd += [f"--repo={repo}"]
        if self.state.edit:
            cmd += ["-e"]
        else:
            if subject:
                cmd += [f"--subject={subject}"]
            if msg:
                cmd += [f"--body={msg}"]
        if branch:
            cmd += [f"--branch={branch}"]
        cmd += [str(root)]
        r = run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r

    def get_sysroot(self):
        """Load the /ostree directory (sysroot)."""
        sysroot = OSTree.Sysroot()
        if not sysroot.load():
            click.secho("Unable to load /sysroot", fg="red")
            sys.exit(1)
        return sysroot

    def open_ostree(self):
        """"Open the ostree repository."""
        if self.state.repo:
            repo = OSTree.Repo.new(Gio.File.new_for_path(str(self.state.repo)))
            if not repo.open(None):
                click.secho(
                    "Opening the archive OSTree repository failed.", fg="red")
                sys.exit(1)
        else:
            sysroot = self.get_sysroot()
            _, repo = sysroot.get_repo()
            if not repo.open():
                click.secho(
                    "Opening the archive OSTree repository failed.", fg="red")
                sys.exit(1)
        return repo

    def get_branch(self):
        """Get a branch in a current deployment."""
        if self.state.branch:
            return self.state.branch
        else:
            sysroot = self.get_sysroot()
            deployment = sysroot.get_booted_deployment()
            origin = deployment.get_origin()
            try:
                refspec = origin.get_string("origin", "refspec")
            except GLib.Error as e:
                # If not a "key not found" error then raise the exception
                if not e.matches(GLib.KeyFile.error_quark(),
                                 GLib.KeyFileError.KEY_NOT_FOUND):
                    raise (e)
                # Fallback to `baserefspec`
                refspec = origin.get_string('origin', 'baserefspec')

            return refspec
