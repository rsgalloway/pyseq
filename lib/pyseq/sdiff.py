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
Contains the main sdiff functions for the pyseq module.
"""

import argparse
import json
import sys

from pyseq.util import resolve_sequence


def diff_sequences(seq1, seq2, compare_size=False):
    """Compares two sequences and returns a dictionary of differences.

    :param seq1: The first sequence to compare.
    :param seq2: The second sequence to compare.
    :param compare_size: Boolean indicating whether to compare disk usage.
    :return: A dictionary containing differences between the two sequences.
    """

    def intval(val):
        try:
            return int(val)
        except:
            return None

    diff = {
        "head": (seq1.head(), seq2.head()),
        "tail": (seq1.tail(), seq2.tail()),
        "pad": (seq1.pad, seq2.pad),
        "start": (seq1.start(), seq2.start()),
        "end": (seq1.end(), seq2.end()),
        "length": (seq1.length(), seq2.length()),
        "missing": {
            "a_only": sorted(set(seq1.missing()) - set(seq2.missing())),
            "b_only": sorted(set(seq2.missing()) - set(seq1.missing())),
        },
    }

    if compare_size:
        disk_a = intval(seq1.format("%d"))
        disk_b = intval(seq2.format("%d"))
        diff["disk_bytes"] = [disk_a, disk_b]
        diff["disk_human"] = [seq1.format("%H"), seq2.format("%H")]

    return diff


def print_diff(diff, compare_size=False):
    """Prints the differences between two sequences.

    :param diff: The dictionary containing differences between sequences.
    :param compare_size: Boolean indicating whether to compare disk usage.
    """

    def show(label, a, b):
        if a != b:
            print(f"{label} mismatch:\n  A: {a}\n  B: {b}")

    show("Head", *diff["head"])
    show("Tail", *diff["tail"])
    show("Padding", *diff["pad"])
    show("Start", *diff["start"])
    show("End", *diff["end"])
    show("Length", *diff["length"])

    a_only = diff["missing"]["a_only"]
    b_only = diff["missing"]["b_only"]
    if a_only:
        print(f"Missing in A: {a_only}")
    if b_only:
        print(f"Missing in B: {b_only}")

    if compare_size and "disk_bytes" in diff:
        a, b = diff["disk_human"]
        if a != b:
            print(f"Disk usage mismatch:\n  A: {a}\n  B: {b}")


def main():
    """Main function to parse arguments and display sequence diffs."""

    parser = argparse.ArgumentParser(
        description="Compare two file sequences and report differences.",
    )
    parser.add_argument(
        "seq1",
        help="First sequence (glob or %%d format)",
    )
    parser.add_argument(
        "seq2",
        help="Second sequence",
    )
    parser.add_argument(
        "--size",
        action="store_true",
        help="Compare disk usage",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    args = parser.parse_args()

    try:
        s1 = resolve_sequence(args.seq1)
        s2 = resolve_sequence(args.seq2)
    except Exception as e:
        print(f"sdiff: error resolving sequence: {e}", file=sys.stderr)
        return 1

    diff = diff_sequences(s1, s2, compare_size=args.size)

    if args.json:
        print(json.dumps(diff, indent=4))
    else:
        print(f"Sequence A: {str(s1)}")
        print(f"Sequence B: {str(s2)}\n")
        print_diff(diff, compare_size=args.size)

    return 0


if __name__ == "__main__":
    sys.exit(main())
