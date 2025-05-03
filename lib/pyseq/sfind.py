#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of the software nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

__doc__ = """
Contains the main sfind functions for the pyseq module.
"""

import argparse
import fnmatch
import os
import sys

import pyseq


def walk_and_collect_sequences(root, include_hidden=False, pattern=None):
    """Recursively walk through the directory tree and collect sequences."""

    for dirpath, dirnames, filenames in os.walk(root):
        if not include_hidden:
            filenames = [f for f in filenames if not f.startswith(".")]
        seqs = pyseq.get_sequences(filenames)
        for seq in seqs:
            full_str = str(seq)
            if pattern and not fnmatch.fnmatch(full_str, pattern):
                continue
            yield os.path.join(dirpath, full_str)


def main():
    """Main function to parse arguments and call the sequence finder."""

    parser = argparse.ArgumentParser(description="Recursively find image sequences")
    parser.add_argument(
        "paths",
        nargs="+",
        help="Directory or directories to search.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="All files are listed (include hidden files).",
    )
    parser.add_argument(
        "-name",
        metavar="PATTERN",
        help="Glob pattern to match sequences (e.g. '*.png').",
    )
    args = parser.parse_args()

    for path in args.paths:
        if not os.path.isdir(path):
            print(f"sfind: {path} is not a directory", file=sys.stderr)
            continue
        for seq in walk_and_collect_sequences(
            path, include_hidden=args.all, pattern=args.name
        ):
            print(seq)

    return 0


if __name__ == "__main__":
    sys.exit(main())
