"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import os
import subprocess

import click


def run_command(cmd,
                debug=False,
                stdin=None,
                stdout=None,
                stderr=None,
                check=True,
                env=None,
                cwd=None):
    """Run a command in a shell."""
    _env = os.environ.copy()
    if env:
        _env.update(env)
    try:
        return subprocess.run(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=_env,
            cwd=cwd,
            check=check,
        )
    except FileNotFoundError:
        click.secho(f"{cmd[0]} not found in PATH.")
    except subprocess.CalledProcessError as e:
        click.secho(f"Failed to run command: {e}")
        raise
