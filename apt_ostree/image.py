"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import shutil

import click

from apt_ostree.log import complete_step
from apt_ostree.log import log_step
from apt_ostree.utils import run_command


class Image:
    def __init__(self, state):
        self.state = state

    def create_image(self):
        """Create a raw disk image from an ostree repository."""
        click.secho(f"Found ostree repository: {self.state.repo}")
        click.secho(f"Found ostree branch: {self.state.branch}")
        with complete_step(f"Setting up workspace for {self.state.branch}"):
            workdir = self.state.workspace.joinpath(
                f"build/{self.state.branch}")
            img_dir = workdir.joinpath("image")
            ostree_repo = img_dir.joinpath("ostree_repo")
            if img_dir.exists():
                shutil.rmtree(img_dir)
            shutil.copytree(
                self.state.base.joinpath("image"),
                img_dir, dirs_exist_ok=True)

        with complete_step("Creating local ostree repository"):
            log_step("Creating image build repository")
            run_command(
                ["ostree", "init", f"--repo={str(ostree_repo)}"],
                cwd=img_dir)
            log_step(f"Pulling {self.state.branch} in image build repository")
            run_command(
                ["ostree", "pull-local", f"--repo={str(ostree_repo)}",
                 str(self.state.repo), str(self.state.branch)],
                cwd=img_dir)
            log_step("Running debos...")

            cmd = ["debos",
                   "-t", f"branch:{self.state.branch}",
                   ]
            if self.state.debug:
                cmd += ["-v"]
            cmd += ["image.yaml"]

            run_command(cmd, cwd=img_dir)

        click.secho(f"Image can be found in {img_dir}")
