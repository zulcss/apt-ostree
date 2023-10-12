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
from gi.repository import Gio, GLib, OSTree  # noqa:H301
from gi.repository.GLib import Variant, VariantDict  # noqa:H301

# Using AT_FDCWD value from fcntl.h
AT_FDCWD = -100


class Ostree:
    def __init__(self, state):
        self.state = state

    def ostree_commit(self,
                      root=None,
                      repo=None,
                      branch=None,
                      subject=None,
                      parent=None,
                      msg=None):
        """Commit rootfs to ostree repository."""
        cmd = ["ostree", "commit"]
        if repo:
            cmd += [f"--repo={repo}"]
        if subject:
            cmd += [f"--subject={subject}"]
        if msg:
            cmd += [f"--body={msg}"]

        if branch:
            cmd += [f"--branch={branch}"]
        if parent:
            cmd += [f"--parent={parent}"]
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

    def ostree_checkout(self, branch, rootfs):
        """Checkout a branch from an ostree repository."""
        repo = self.open_ostree()
        ret, rev = repo.resolve_rev(branch, True)
        opts = OSTree.RepoCheckoutAtOptions()
        if rev:
            try:
                repo.checkout_at(opts, AT_FDCWD, str(rootfs), rev, None)
            except GLib.GError as e:
                click.secho(f"Failed to checkout {rev}: {e.message}", fg="red")
                raise

    def ostree_ref(self, branch):
        """Find the commit id for a given reference."""
        repo = self.open_ostree()
        ret, rev = repo.resolve_rev(branch, True)
        if not rev:
            click.secho(f"{branch} not found in {self.state.repo}", fg="red")
            sys.exit(1)
        return rev

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
                # If not a "key not found" error then
                # raise the exception
                if not e.matches(GLib.KeyFile.error_quark(),
                                 GLib.KeyFileError.KEY_NOT_FOUND):
                    raise (e)
                # Fallback to `baserefspec`
                refspec = origin.get_string('origin', 'baserefspec')

            return refspec

    def remotes_list(self):
        """Fetch list of remote hosts."""
        try:
            repo = self.open_ostree()
            remotes = repo.remote_list()
            return remotes
        except GLib.GError as e:
            click.secho(f"Failed to fetch remotes: {e}")

    def get_remote_url(self, remote):
        """Fetch the URL of a remote."""
        repo = self.open_ostree()
        _, url = repo.remote_get_url(remote)
        return url

    def remote_add(self):
        """Setup a remote given a URL."""
        with self.console.status(f"Adding remote {self.state.remote}"):
            repo = self.open_ostree()

            # Turn off gpg verification for now.
            options = None
            vd = VariantDict.new()
            vd.insert_value('gpg-verify', Variant.new_boolean(False))
            options = vd.end()

            try:
                check = repo.remote_change(
                    None,
                    OSTree.RepoRemoteChange.ADD_IF_NOT_EXISTS,
                    self.state.remote,
                    self.state.url,
                    options,
                    None)
                if check:
                    self.console.print(
                        f"Successfully added {self.state.remote}.")
            except GLib.GError as e:
                click.secho(f"Failed to add remote: {e}")

    def remote_remove(self):
        """Delete a remote."""
        try:
            repo = self.open_ostree()
            check = repo.remote_delete(self.state.remote, None)
            if check:
                self.console.print(
                    f"Successfully removed {self.state.remote}.")
        except GLib.GError as e:
            click.secho(f"Failed to remove remote: {e}")

    def remote_refs(self, remote):
        try:
            repo = self.open_ostree()
            _, refs = repo.remote_list_refs(remote)
            return refs
        except GLib.GError as e:
            click.secho(f"Failed to fetch refs: {e}")
            sys.exit(1)
