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


def run_sandbox_command(
    args,
    rootfs,
    stdin=None,
    stdout=None,
    stderr=None,
    check=True,
    env=None
):
    """Run a shell wrapped with bwrap."""
    cmd = [
        "bwrap",
        "--proc", "/proc",
        "--dev", "/dev",
        "--dir", "/run",
        "--dir", "/usr/etc",
        "--symlink", "usr/etc", "/etc",
        "--bind", "/tmp", "/tmp",
        "--bind", f"{rootfs}/usr", "/usr",
        "--bind", f"{rootfs}/usr/etc", "/usr/etc",
        "--bind", f"{rootfs}/usr/rootdirs/var", "/var",
        "--symlink", "/usr/lib", "/lib",
        "--symlink", "/usr/lib64", "/lib64",
        "--symlink", "/usr/bin", "/bin",
        "--symlink", "/usr/sbin", "/sbin",
        "--share-net",
        "--die-with-parent",
        "--chdir", "/",
    ]
    cmd += args

    return run_command(
        cmd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        check=check,
        env=env,
    )
