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
Contains the main smove functions for the pyseq module.
"""

import sys
import os
import argparse
import shutil
import fnmatch
import re
from typing import Optional

import pyseq
from pyseq.util import (
    cli_catch_keyboard_interrupt,
    is_compressed_format_string,
    resolve_sequence,
)


def move_sequence(
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
    """Move a sequence of files from one directory to another.

    :param seq: The sequence object to move.
    :param src_dir: The source directory containing the files.
    :param dest_dir: The destination directory to move the files to.
    :param rename: New basename for the files.
    :param renumber: New starting frame number.
    :param pad: Number of digits to pad the frame number.
    :param force: Overwrite existing files if True.
    :param dryrun: If True, only print the actions without executing them.
    :param verbose: If True, print detailed information about the actions.
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
            shutil.move(src_path, dest_path)


def resolve_source_sequence(source: str):
    """Resolve a source string into a sequence and its containing directory."""
    if is_compressed_format_string(source):
        seq = resolve_sequence(source)
        dirname = os.path.dirname(source) or "."
        return seq, dirname

    dirname = os.path.dirname(source) or "."
    basename = os.path.basename(source)
    matches = [f for f in os.listdir(dirname) if fnmatch.fnmatchcase(f, basename)]
    sequences = pyseq.get_sequences(matches)
    if not sequences:
        raise FileNotFoundError(f"No sequence found matching {source}")
    if len(sequences) > 1:
        raise ValueError(f"Multiple sequences found matching {source}: {sequences}")
    return sequences[0], dirname


def parse_destination(destination: str):
    """Parse a destination string as either a directory or sequence template."""
    if not is_compressed_format_string(destination):
        return {
            "kind": "directory",
            "dest_dir": destination,
            "rename": None,
            "pad": None,
        }

    filename = os.path.basename(destination)
    match = re.search(r"%(?:0(?P<pad>\d+))?d", filename)
    if not match:
        raise ValueError(f"Invalid destination sequence pattern: {destination}")

    dest_dir = os.path.dirname(destination) or "."
    rename = filename[: match.start()]
    tail = filename[match.end() :]
    pad = int(match.group("pad")) if match.group("pad") else None

    return {
        "kind": "sequence",
        "dest_dir": dest_dir,
        "rename": rename,
        "pad": pad,
        "tail": tail,
    }


@cli_catch_keyboard_interrupt
def main():
    """Main function to handle command line arguments and call the move_sequence."""

    parser = argparse.ArgumentParser(
        description="Move image sequences with renaming/renumbering support",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Source sequence(s) followed by a destination directory or sequence pattern",
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
        help="Preview move without performing it",
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

    try:
        dest_spec = parse_destination(dest)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if len(sources) > 1 and dest_spec["kind"] != "directory":
        print(
            "Error: destination must be a directory when moving multiple sources",
            file=sys.stderr,
        )
        return 1

    for source in sources:
        try:
            seq, dirname = resolve_source_sequence(source)

            rename = args.rename
            pad = args.pad
            dest_dir = dest_spec["dest_dir"]

            if dest_spec["kind"] == "sequence":
                rename = dest_spec["rename"]
                pad = dest_spec["pad"] if dest_spec["pad"] is not None else pad
                if dest_spec["tail"] != seq.tail():
                    raise ValueError(
                        "Destination sequence pattern must preserve the source extension"
                    )

            move_sequence(
                seq,
                dirname,
                dest_dir,
                rename=rename,
                renumber=args.renumber,
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
