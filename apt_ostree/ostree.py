"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging
import subprocess
import sys

from rich.console import Console

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
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.console = Console()

    def init(self):
        """Create a new ostree repo."""
        repo = OSTree.Repo.new(Gio.File.new_for_path(
            str(self.state.repo)))
        mode = OSTree.RepoMode.ARCHIVE_Z2

        try:
            repo.create(mode)
            self.console.print("Sucessfully initialized ostree repository.")
        except GLib.GError as e:
            self.logging.error(f"Failed to create repo: {e}")
            sys.exit(1)

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
        if r.returncode != 0:
            self.logging.error("Failed to commit to tree.")
            sys.exit(1)
        self.logging.info(f"Sucessfully commited to {branch}.")
        return r

    def get_sysroot(self):
        """Load the /ostree directory (sysroot)."""
        sysroot = OSTree.Sysroot()
        if not sysroot.load():
            self.logging.error("Unable to load /sysroot.")
            sys.exit(1)
        return sysroot

    def open_ostree(self):
        """"Open the ostree repository."""
        if self.state.repo:
            repo = OSTree.Repo.new(Gio.File.new_for_path(str(self.state.repo)))
            if not repo.open(None):
                self.logging.error(
                    "Opening the archive OSTree repository failed.")
                sys.exit(1)
        else:
            sysroot = self.get_sysroot()
            _, repo = sysroot.get_repo()
            if not repo.open():
                self.logging.error(
                    "Opening the archive OSTree repository failed.")
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
                self.logging.error(f"Failed to checkout {rev}: {e.message}")
                raise

    def ostree_ref(self, branch):
        """Find the commit id for a given reference."""
        repo = self.open_ostree()
        ret, rev = repo.resolve_rev(branch, True)
        if not rev:
            self.logging.error(f"{branch} not found in {self.state.repo}")
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
            self.logging.error(f"Failed to fetch remotes: {e}")

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
                    self.looging.info(
                        f"Successfully added {self.state.remote}.")
            except GLib.GError as e:
                self.logging.warning(f"Failed to add remote: {e}")

    def remote_remove(self):
        """Delete a remote."""
        try:
            repo = self.open_ostree()
            check = repo.remote_delete(self.state.remote, None)
            if check:
                self.logging.info(
                    f"Successfully removed {self.state.remote}.")
        except GLib.GError as e:
            self.logging.error(f"Failed to remove remote: {e}")

    def remote_refs(self, remote):
        try:
            repo = self.open_ostree()
            _, refs = repo.remote_list_refs(remote)
            return refs
        except GLib.GError as e:
            self.logging.error(f"Failed to fetch refs: {e}")
            sys.exit(1)
