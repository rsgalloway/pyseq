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
from typing import Optional

import pyseq
from pyseq.util import (
    cli_catch_keyboard_interrupt,
    parse_destination_reference,
    resolve_sequence_reference,
)


def copy_sequence(
    seq: pyseq.Sequence,
    src_dir: str,
    dest_dir: str,
    rename: Optional[str] = None,
    renumber: Optional[int] = None,
    pad: Optional[int] = None,
    force: bool = False,
    dryrun: bool = False,
    verbose: bool = False,
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


@cli_catch_keyboard_interrupt
def main():
    """Main function to parse cli args and copy sequences."""

    parser = argparse.ArgumentParser(
        description="Copy image sequences with destination-based renaming and renumbering support",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Source sequence(s) followed by a destination directory or sequence pattern",
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

    if len(args.paths) < 2:
        print("Error: expected at least one source and a destination", file=sys.stderr)
        return 1

    sources = args.paths[:-1]
    dest = args.paths[-1]

    for source in sources:
        try:
            seq, dirname = resolve_sequence_reference(source)
            dest_spec = parse_destination_reference(dest, seq)

            if len(sources) > 1 and dest_spec["kind"] != "directory":
                raise ValueError(
                    "destination must be a directory when copying multiple sources"
                )

            rename = dest_spec["rename"]
            pad = args.pad if dest_spec["kind"] == "directory" else dest_spec["pad"]
            renumber = (
                args.renumber
                if dest_spec["kind"] == "directory"
                else dest_spec["renumber"]
            )

            copy_sequence(
                seq,
                dirname,
                dest_spec["dest_dir"],
                rename=rename,
                renumber=renumber,
                pad=pad,
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
