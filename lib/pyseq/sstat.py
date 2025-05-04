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
Contains the main sstat functions for the pyseq module.
"""

import argparse
import datetime
import json
import os
import sys

import pyseq
from pyseq.util import resolve_sequence


def format_time(ts: int):
    """Format a timestamp into a human-readable string.

    :param ts: The timestamp to format.
    :return: A formatted string representing the timestamp.
    """
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S %z")
    except Exception:
        return "-"


def print_sstat(seq: pyseq.Sequence):
    """Prints the statistics of a sequence.

    :param seq: The pyseq.Sequence object to print statistics for.
    """

    def stat_path(frame):
        return os.stat(os.path.join(seq.format("%D"), frame.name))

    try:
        st_first = stat_path(seq[0])
        st_last = stat_path(seq[-1])
    except Exception as e:
        print(f"Error: cannot stat frame: {e}", file=sys.stderr)
        return

    def format_time_range(t1, t2):
        return f"{format_time(t1)}.. {format_time(t2)}"

    print(f"Sequence: {str(seq)}")
    print(
        f"Size:     {seq.format('%H'):>8}    Frames: {seq.format('%l'):>5}    Padding: {seq.pad}"
    )
    missing = seq.format("%M")
    print(f"Missing:  {missing if missing else 'none'}")
    print(f"Head:     {seq.head()}")
    print(f"Tail:     {seq.tail()}")
    print(f"Range:    {seq.format('%r')}")
    print(f"Blocks:   {st_first.st_blocks + st_last.st_blocks}")
    print(f"Access:   {format_time_range(st_first.st_atime, st_last.st_atime)}")
    print(f"Modify:   {format_time_range(st_first.st_mtime, st_last.st_mtime)}")
    print(f"Change:   {format_time_range(st_first.st_ctime, st_last.st_ctime)}")


def json_sstat(seq: pyseq.Sequence):
    """Convert sequence statistics to JSON format.

    :param seq: The sequence object to convert to JSON.
    :return: A dictionary containing the sequence statistics.
    """
    st_first = os.stat(os.path.join(seq.format("%D"), seq[0].name))
    st_last = os.stat(os.path.join(seq.format("%D"), seq[-1].name))

    return {
        "sequence": str(seq),
        "head": seq.head(),
        "tail": seq.tail(),
        "start": seq.start(),
        "end": seq.end(),
        "length": seq.length(),
        "pad": seq.pad,
        "range": seq.format("%r"),
        "missing": seq.missing(),
        "size_bytes": seq.format("%d"),
        "size_human": seq.format("%H").strip(),
        "access": {
            "first": format_time(st_first.st_atime),
            "last": format_time(st_last.st_atime),
        },
        "modify": {
            "first": format_time(st_first.st_mtime),
            "last": format_time(st_last.st_mtime),
        },
        "change": {
            "first": format_time(st_first.st_ctime),
            "last": format_time(st_last.st_ctime),
        },
    }


def main():
    """Main function to parse arguments and display sequence statistics."""

    parser = argparse.ArgumentParser(
        description="Display stat-like metadata about a file sequence.\n"
        "Supports compressed strings (e.g. 'foo.%04d.exr') or glob inputs.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "sequence",
        help="Input sequence as glob or compressed pattern (e.g. 'foo.%%04d.exr')",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output metadata as JSON",
    )
    args = parser.parse_args()

    try:
        seq = resolve_sequence(args.sequence)
        if args.json:
            data = json_sstat(seq)
            print(json.dumps(data, indent=4))
        else:
            print_sstat(seq)
    except Exception as e:
        print(f"sstat: error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
