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
Contains the main scopy functions for the pyseq module.
"""

import sys
import os
import argparse
import shutil
import fnmatch
import pyseq
import re

from pyseq.util import resolve_sequence


def is_compressed_format_string(s: str) -> bool:
    """Check if the string is a compressed format string. A compressed format
    string is a string that contains a format specifier for integers, such as
    "%d" or "%0Nd", where N is a digit.

    :param s: The string to check.
    :return: True if the string is a compressed format string, False otherwise.
    """
    return "%d" in s or re.search(r"%0\d+d", s)


def copy_sequence(
    seq,
    src_dir,
    dest_dir,
    rename=None,
    renumber=None,
    pad=None,
    force=False,
    dryrun=False,
    verbose=False,
):
    """Copy a sequence of files from src_dir to dest_dir.

    :param seq: The sequence object to copy.
    :param src_dir: The source directory containing the files.
    :param dest_dir: The destination directory to copy files to.
    :param rename: Optional new basename for the copied files.
    :param renumber: Optional new starting frame number.
    :param pad: Optional number of digits for padding the frame numbers.
    :param force: If True, overwrite existing files.
    :param dryrun: If True, print the operations without executing them.
    :param verbose: If True, print detailed information about the operations.
    """
    dest_basename = rename or seq.head()
    dest_pad = pad or seq.pad
    start_frame = renumber or seq.start()

    for i, frame in enumerate(seq):
        src_path = os.path.join(src_dir, frame.name)
        frame_num = start_frame + i
        dest_frame_name = f"{dest_basename}{frame_num:0{dest_pad}d}{seq.tail()}"
        dest_path = os.path.join(dest_dir, dest_frame_name)

        if verbose or dryrun:
            print(f"{src_path} -> {dest_path}")

        if not dryrun:
            os.makedirs(dest_dir, exist_ok=True)
            if os.path.exists(dest_path) and not force:
                print(
                    f"File exists: {dest_path} (use --force to overwrite)",
                    file=sys.stderr,
                )
                continue
            shutil.copy2(src_path, dest_path)


def main():
    """Main function to parse cli args and copy sequences."""

    parser = argparse.ArgumentParser(
        description="Copy image sequences with renaming/renumbering support"
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help="Source sequences (wildcards or compressed format strings)",
    )
    parser.add_argument(
        "dest",
        help="Destination directory",
    )
    parser.add_argument(
        "--rename",
        help="Rename sequence basename",
    )
    parser.add_argument(
        "--renumber",
        type=int,
        help="New starting frame",
    )
    parser.add_argument(
        "--pad",
        type=int,
        help="Padding digits",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "-d",
        "--dryrun",
        action="store_true",
        help="Preview copy without performing it",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dest):
        print(f"Error: destination {args.dest} is not a directory", file=sys.stderr)
        sys.exit(1)

    for source in args.sources:
        try:
            if is_compressed_format_string(source):
                seq = resolve_sequence(source)
                dirname = os.path.dirname(source) or "."
            else:
                # treat as glob
                dirname = os.path.dirname(source) or "."
                basename = os.path.basename(source)
                matches = [
                    f for f in os.listdir(dirname) if fnmatch.fnmatchcase(f, basename)
                ]
                sequences = pyseq.get_sequences(matches)
                if not sequences:
                    print(f"No sequence found matching {source}", file=sys.stderr)
                    continue
                seq = sequences[0]

            copy_sequence(
                seq,
                dirname,
                args.dest,
                rename=args.rename,
                renumber=args.renumber,
                pad=args.pad,
                force=args.force,
                dryrun=args.dryrun,
                verbose=args.verbose,
            )

        except Exception as e:
            print(f"Error processing {source}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
