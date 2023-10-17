"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import pathlib

import click

from apt_ostree.cmd import State

"""global options"""


def debug_option(f):
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.debug = value
        return value
    return click.option(
        "--debug",
        is_flag=True,
        help="Increase verbosity",
        callback=callback
    )(f)


def workspace_option(f):
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.workspace = pathlib.Path(value)
        return value
    return click.option(
        "--workspace",
        help="Path to the apt-ostree workspace",
        nargs=1,
        default="/var/tmp/apt-ostree",
        required=True,
        callback=callback
    )(f)


"""compose options"""


def repo_option(f):
    """ostree repo path option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.repo = pathlib.Path(value)
        return value
    return click.option(
        "--repo",
        help="Path to the Ostree Repository",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def base_option(f):
    """apt-ostree configuration directory option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.base = pathlib.Path(value)
        return value
    return click.option(
        "--base",
        help="Path to the apt-ostree configuration directory",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def branch_option(f):
    """apt-ostree configuration directory option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.branch = value
        return value
    return click.option(
        "--branch",
        help="Ostree branch to use",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def branch_argument(f):
    """ostree branch option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.branch = value
        return value
    return click.argument(
        "branch",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def compose_options(f):
    f = repo_option(f)
    f = base_option(f)
    f = branch_argument(f)
    return f


"""Package feed options"""


def feed_option(f):
    """package feed directory"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.feed = pathlib.Path(value)
        return value
    return click.option(
        "--feed",
        help="Directory to store package repository",
        nargs=1,
        required=True,
        default="/var/repository",
        callback=callback
    )(f)


def release_option(f):
    """release option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.release = value
        return value
    return click.option(
        "--release",
        help="Debian codename release",
        nargs=1,
        required=True,
        callback=callback,
        type=click.Choice(["bookworm", "bullseye"]),
    )(f)


def origin_option(f):
    """Origin option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.origin = value
        return value
    return click.option(
        "--origin",
        help="Debian package origin (e.g. updates)",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def source_option(f):
    """Repo source line option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.sources = value
        return value
    return click.option(
        "--sources",
        help="Repo source list",
        nargs=1,
        required=True,
        callback=callback
    )(f)


def enablerepo_option(f):
    """Enable Debian package feed."""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.enable = value
        return value
    return click.option(
        "--enablerepo",
        help="Enable repo source",
        is_flag=True,
        default=False,
        required=True,
        callback=callback
    )(f)


def disablerepo_option(f):
    """Disable Debian package feed."""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.disable = value
        return value
    return click.option(
        "--disablerepo",
        help="Disable Repo source",
        is_flag=True,
        default=False,
        required=True,
        callback=callback
    )(f)


"""packages"""


def packages_option(f):
    """packages option"""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.packages = value
        return value
    return click.argument(
        "packages",
        nargs=-1,
        callback=callback,
        required=True,
    )(f)


"""remotes"""


def remote_option(f):
    """Name of remote host."""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.remote = value
        return value
    return click.option(
        "--remote",
        help="Remote stie",
        callback=callback
    )(f)


def url_option(f):
    """Name of remote host."""
    def callback(ctxt, param, value):
        state = ctxt.ensure_object(State)
        state.url = value
        return value
    return click.option(
        "--url",
        help="Site URL",
        required=True,
        callback=callback
    )(f)
