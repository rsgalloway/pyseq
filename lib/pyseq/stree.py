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
Contains the main stree functions for the pyseq module.
"""

import argparse
import os
import sys

import pyseq


def print_tree(root, prefix="", include_hidden=False):
    """Recursively prints the directory tree of the given root directory.

    :param root: The root directory to start printing from.
    :param prefix: The prefix to use for each line of the tree.
    """
    try:
        entries = os.listdir(root)
    except OSError as e:
        print(f"{prefix}[error opening {root}: {e}]", file=sys.stderr)
        return

    if not include_hidden:
        entries = [e for e in entries if not e.startswith(".")]

    files = [e for e in entries if os.path.isfile(os.path.join(root, e))]
    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e))]

    seqs = pyseq.get_sequences(files)
    total = len(dirs) + len(seqs)

    for i, name in enumerate(dirs + [str(s) for s in seqs]):
        is_last = i == total - 1
        connector = "└── " if is_last else "├── "
        next_prefix = prefix + ("    " if is_last else "│   ")
        print(f"{prefix}{connector}{name}")

        if name in dirs:
            print_tree(os.path.join(root, name), next_prefix, include_hidden)


def main():
    """Main function to parse cli args and print the directory tree."""

    parser = argparse.ArgumentParser(description="Display tree of sequences")
    parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        help="Root directory.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="All files are listed (include hidden files).",
    )
    args = parser.parse_args()

    print(args.path)
    print_tree(args.path, include_hidden=args.all)


if __name__ == "__main__":
    main()
