#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Lightweight helpers shared by CLI entry points."""

import functools
import sys


def cli_catch_keyboard_interrupt(func):
    """Return exit code 1 instead of a traceback on Ctrl-C."""

    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("stopping...", file=sys.stderr)
            return 1

    return inner
