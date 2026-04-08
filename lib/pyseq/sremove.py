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
Contains the main sremove functions for the pyseq module.
"""

import argparse
import os
import sys

import pyseq
from pyseq.util import cli_catch_keyboard_interrupt, resolve_sequence_reference


def remove_sequence(
    seq: pyseq.Sequence,
    src_dir: str,
    force: bool = False,
    dryrun: bool = False,
    verbose: bool = False,
):
    """Remove a sequence of files from src_dir."""
    for frame in seq:
        src_path = os.path.join(src_dir, frame.name)

        if verbose or dryrun:
            print(src_path)

        if dryrun:
            continue

        try:
            os.remove(src_path)
        except FileNotFoundError:
            if not force:
                raise


@cli_catch_keyboard_interrupt
def main():
    """Main function to parse cli args and remove sequences."""
    parser = argparse.ArgumentParser(
        description="Remove image sequences resolved from patterns, ranges, or globs",
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help="Source sequences (globs, compressed patterns, or explicit ranges)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ignore missing files",
    )
    parser.add_argument(
        "-d",
        "--dryrun",
        action="store_true",
        help="Preview removals without performing them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    for source in args.sources:
        try:
            seq, dirname = resolve_sequence_reference(source)
            remove_sequence(
                seq,
                dirname,
                force=args.force,
                dryrun=args.dryrun,
                verbose=args.verbose,
            )
        except Exception as e:
            print(f"Error processing {source}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
