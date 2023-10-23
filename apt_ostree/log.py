"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0
"""

import logging

from rich.console import Console
from rich.logging import RichHandler
from systemd.journal import JournalHandler


def setup_log(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(message)s"

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.NOTSET)

    journald_handler = JournalHandler(
        SYSLOG_IDENTIFIER="apt-ostree")
    journald_handler.setLevel(level)
    journald_handler.setFormatter(logging.Formatter(
        '[%(levelname)s] %(message)s'))
    rootLogger.addHandler(journald_handler)

    console = Console(highlight=False)

    rich_handler = RichHandler(show_path=False,
                               show_time=False,
                               show_level=False,
                               console=console)
    rich_handler.setLevel(level)
    rich_handler.setFormatter(logging.Formatter(fmt))
    rootLogger.addHandler(rich_handler)

    return rootLogger
