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
import glob
import os
import re
import warnings

import pyseq


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


def _natural_key(x):
    """Splits a string into characters and digits.

    :param x: The string to be split.
    :return: A list of characters and digits.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", x)]


def _ext_key(x):
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
def natural_sort(items):
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
        raise ValueError("Format string must contain '%d' or '%0Nd'")

    padding = match.group(1)
    if padding:
        pad = int(padding)
        glob_part = filename.replace(f"%0{pad}d", "?" * pad)
    else:
        glob_part = filename.replace("%d", "*")

    glob_pattern = os.path.join(directory, glob_part)
    matches = glob.glob(glob_pattern)

    if not matches:
        raise FileNotFoundError(f"No files match pattern: {sequence_string}")

    # pass full paths to get_sequences
    sequences = pyseq.get_sequences(matches)
    if not sequences:
        raise ValueError("No valid sequences found")
    elif len(sequences) > 1:
        raise ValueError("Multiple sequences found")

    return sequences[0]
