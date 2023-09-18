"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import subprocess

from apt_ostree.utils import run_command


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
        if subject:
            cmd += [f"--subject={subject}"]
        if msg:
            cmd += [f"--body={msg}"]
        if branch:
            cmd += [f"--branch={branch}"]
        cmd += [str(root)]
        r = run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r
