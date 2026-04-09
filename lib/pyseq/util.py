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

import functools
import fnmatch
import glob
import os
import re
import sys
import warnings
from typing import Optional

import pyseq
from pyseq.config import range_join


def deprecated(func):
    """Deprecation warning decorator."""

    def inner(*args, **kwargs):
        warnings.warn(
            "Call to deprecated method {}".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    inner.__name__ = func.__name__
    inner.__doc__ = func.__doc__
    inner.__dict__.update(func.__dict__)
    return inner


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


def _natural_key(x: str):
    """Splits a string into characters and digits.

    :param x: The string to be split.
    :return: A list of characters and digits.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", x)]


def _ext_key(x: str):
    """Similar to `_natural_key` except this one uses the file extension at
    the head of split string.  This fixes issues with files that are named
    similar but with different file extensions:

    This example:

        file.001.jpg
        file.001.tiff
        file.002.jpg
        file.002.tiff

    Would get properly sorted into:

        file.001.jpg
        file.002.jpg
        file.001.tiff
        file.002.tiff
    """
    name, ext = os.path.splitext(x)
    return [ext] + _natural_key(name)


def is_compressed_format_string(s: str) -> bool:
    """Check if the string is a compressed format string. A compressed format
    string is a string that contains a format specifier for integers, such as
    "%d" or "%0Nd", where N is a digit.

    :param s: The string to check.
    :return: True if the string is a compressed format string, False otherwise.
    """
    return "%d" in s or re.search(r"%0\d+d", s)


@functools.lru_cache(maxsize=None)
def natural_sort(items: list):
    """
    Sorts a list of items in natural order.

    :param items: The list of items to be sorted.
    :return: The sorted list of items.
    """
    return sorted(items, key=_natural_key)


def resolve_sequence(sequence_string: str):
    """Given a compressed sequence string like 'file.%04d.png' or
    '/path/to/file.%04d.png', return a `Sequence` object of matching files on
    disk.

    :param sequence_string: The compressed sequence string to be uncompressed.
    :return: A pyseq.Sequence object of matching files.
    """

    # split directory and filename
    directory = os.path.dirname(sequence_string) or "."
    filename = os.path.basename(sequence_string)

    # detect %d or %0Nd
    match = re.search(r"%0?(\d*)d", filename)
    if not match:
        raise ValueError("Sequence string must contain '%d' or '%0Nd'")

    padding = match.group(1)
    if padding:
        pad = int(padding)
        glob_part = filename.replace(f"%0{pad}d", "?" * pad)
        regex_pattern = re.escape(filename).replace(
            f"%0{pad}d", r"\d{" + str(pad) + r"}"
        )
    else:
        glob_part = filename.replace("%d", "*")
        regex_pattern = re.escape(filename).replace("%d", r"\d+")

    # glob all files in the directory using glob pattern
    glob_pattern = os.path.join(directory, glob_part)
    candidate_files = glob.glob(glob_pattern)

    # filter using regex (because glob pattern is wide)
    regex = re.compile(f"^{regex_pattern}$")
    matches = [f for f in candidate_files if regex.match(os.path.basename(f))]

    if not matches:
        raise FileNotFoundError(f"No files match pattern: {sequence_string}")

    # pass full paths to get_sequences
    sequences = pyseq.get_sequences(matches)
    if not sequences:
        raise ValueError("No valid sequences found")
    elif len(sequences) > 1:
        raise ValueError("Multiple sequences found: %s" % sequences)

    return sequences[0]


def build_sequence_pattern(head: str, pad: Optional[int], tail: str) -> str:
    """Build a compressed sequence pattern from sequence components."""
    if pad:
        return f"{head}%0{pad}d{tail}"
    return f"{head}%d{tail}"


def subset_sequence(seq, frames):
    """Return a sequence containing only the requested frames."""
    frame_set = set(frames)
    items = [item for item in seq if item.frame in frame_set]
    found_frames = {item.frame for item in items}
    missing_frames = sorted(frame_set - found_frames)
    if missing_frames:
        raise FileNotFoundError(f"Missing frames in sequence: {missing_frames}")

    sequences = pyseq.get_sequences(items)
    if not sequences:
        raise ValueError("No valid sequence found for requested frame subset")
    return sequences[0]


def parse_explicit_sequence_string(reference: str):
    """Parse a serialized sequence string, including embedded range syntax."""
    dirname = os.path.dirname(reference) or "."
    basename = os.path.basename(reference)

    embedded = re.match(
        r"^(?P<head>.+?)(?P<range>\[(?:[^\]]+)\]|\d+-\d+)(?P<tail>\.[^/\s]+)$",
        basename,
    )
    if embedded:
        range_text = embedded.group("range")
        frames = []
        if range_text.startswith("["):
            for number_group in range_text[1:-1].split(range_join):
                number_group = number_group.strip()
                if not number_group:
                    continue
                if "-" in number_group:
                    start, end = number_group.split("-", 1)
                    frames.extend(range(int(start), int(end) + 1))
                else:
                    frames.append(int(number_group))
        else:
            start, end = range_text.split("-", 1)
            frames = list(range(int(start), int(end) + 1))

        items = [
            pyseq.Item(
                os.path.join(
                    dirname,
                    f"{embedded.group('head')}{frame}{embedded.group('tail')}",
                )
            )
            for frame in frames
        ]
        sequences = pyseq.get_sequences(items)
        if sequences:
            return {
                "seq": sequences[0],
                "has_pad": False,
            }

    formats = (
        ("%h%p%t %R", True),
        ("%h%p%t %r", True),
        ("%h%R%t", False),
        ("%h%r%t", False),
    )
    for fmt, has_pad in formats:
        seq = pyseq.uncompress(reference, fmt=fmt)
        if seq:
            return {
                "seq": seq,
                "has_pad": has_pad,
            }
    return None


def resolve_sequence_reference(reference: str):
    """Resolve a source reference into a sequence and its containing directory."""
    explicit = parse_explicit_sequence_string(reference)
    if explicit:
        dirname = os.path.dirname(reference) or "."
        requested_seq = explicit["seq"]

        if explicit["has_pad"]:
            pattern = os.path.join(
                dirname,
                build_sequence_pattern(
                    requested_seq.head(),
                    requested_seq.pad,
                    requested_seq.tail(),
                ),
            )
            full_seq = resolve_sequence(pattern)
        else:
            sequences = pyseq.get_sequences(os.listdir(dirname))
            candidates = [
                seq
                for seq in sequences
                if seq.head() == requested_seq.head()
                and seq.tail() == requested_seq.tail()
            ]
            candidates = [
                seq
                for seq in candidates
                if set(requested_seq.frames()).issubset(set(seq.frames()))
            ]
            if not candidates:
                raise FileNotFoundError(f"No sequence found matching {reference}")
            if len(candidates) > 1:
                raise ValueError(
                    f"Multiple sequences found matching {reference}: {candidates}"
                )
            full_seq = candidates[0]

        return subset_sequence(full_seq, requested_seq.frames()), dirname

    if is_compressed_format_string(reference):
        seq = resolve_sequence(reference)
        dirname = os.path.dirname(reference) or "."
        return seq, dirname

    dirname = os.path.dirname(reference) or "."
    basename = os.path.basename(reference)
    matches = [f for f in os.listdir(dirname) if fnmatch.fnmatchcase(f, basename)]
    sequences = pyseq.get_sequences(matches)
    if not sequences:
        raise FileNotFoundError(f"No sequence found matching {reference}")
    if len(sequences) > 1:
        raise ValueError(f"Multiple sequences found matching {reference}: {sequences}")
    return sequences[0], dirname


def parse_destination_reference(destination: str, source_seq):
    """Parse a destination string as either a directory or destination sequence."""
    explicit = parse_explicit_sequence_string(destination)
    if explicit:
        dest_seq = explicit["seq"]
        dest_frames = list(dest_seq.frames())
        expected_frames = list(range(dest_frames[0], dest_frames[0] + len(source_seq)))

        if dest_seq.tail() != source_seq.tail():
            raise ValueError(
                "Destination sequence pattern must preserve the source extension"
            )
        if dest_frames != expected_frames:
            raise ValueError("Destination explicit range must be contiguous")
        if len(dest_seq) != len(source_seq):
            raise ValueError("Destination explicit range must match source length")

        return {
            "kind": "sequence",
            "dest_dir": os.path.dirname(destination) or ".",
            "rename": dest_seq.head(),
            "pad": dest_seq.pad if explicit["has_pad"] else None,
            "renumber": dest_frames[0],
        }

    if not is_compressed_format_string(destination):
        return {
            "kind": "directory",
            "dest_dir": destination,
            "rename": None,
            "pad": None,
            "renumber": None,
        }

    filename = os.path.basename(destination)
    match = re.search(r"%(?:0(?P<pad>\d+))?d", filename)
    if not match:
        raise ValueError(f"Invalid destination sequence pattern: {destination}")

    tail = filename[match.end() :]
    if tail != source_seq.tail():
        raise ValueError(
            "Destination sequence pattern must preserve the source extension"
        )

    return {
        "kind": "sequence",
        "dest_dir": os.path.dirname(destination) or ".",
        "rename": filename[: match.start()],
        "pad": int(match.group("pad")) if match.group("pad") else None,
        "renumber": None,
    }
