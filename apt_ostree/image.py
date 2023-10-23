"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging
import shutil

from rich.console import Console

from apt_ostree.utils import run_command


class Image:
    def __init__(self, state):
        self.logging = logging.getLogger(__name__)
        self.console = Console()
        self.state = state

    def create_image(self):
        """Create a raw disk image from an ostree repository."""
        self.logging.info(f"Found ostree repository: {self.state.repo}")
        self.logging.info(f"Found ostree branch: {self.state.branch}")
        with self.console.status(
                f"Setting up workspace for {self.state.branch}."):
            workdir = self.state.workspace.joinpath(
                f"build/{self.state.branch}")
            img_dir = workdir.joinpath("image")
            ostree_repo = img_dir.joinpath("ostree_repo")
            if img_dir.exists():
                shutil.rmtree(img_dir)
            shutil.copytree(
                self.state.base.joinpath("image"),
                img_dir, dirs_exist_ok=True)

        self.logging.info("Creating image build repository")
        run_command(
            ["ostree", "init", f"--repo={str(ostree_repo)}"],
            cwd=img_dir)
        self.logging.info(
            f"Pulling {self.state.branch} in image build repository")
        run_command(
            ["ostree", "pull-local", f"--repo={str(ostree_repo)}",
             str(self.state.repo), str(self.state.branch)],
            cwd=img_dir)
        self.logging.info("Running debos...")

        cmd = [
            "debos",
            "-t", f"branch:{self.state.branch}",
        ]
        if self.state.debug:
            cmd += ["-v"]
        cmd += ["image.yaml"]

        run_command(cmd, cwd=img_dir)

        self.logging.info(f"Image can be found in {img_dir}")
