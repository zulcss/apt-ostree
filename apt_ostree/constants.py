"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

VERSION = "0.1"

# packages to exclude from systemd-tmpfiles check.
excluded_packages = [
    "ucf",
    "base-files",
    "systemd",
    "init-system-helpers",
    "dbus",
    "policykit-1",
    "polkitd",
    "debconf"
]
