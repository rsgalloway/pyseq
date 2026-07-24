#!/usr/bin/env python
#
# Copyright (c) 2011-2026, Ryan Galloway (ryan@rsgalloway.com)
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
Contains pyseq configs and default settings.
"""

import os
import re

# default serialization format string
DEFAULT_FORMAT = "%h%r%t"
default_format = os.getenv("PYSEQ_DEFAULT_FORMAT", DEFAULT_FORMAT)

# default serialization format string for global sequences
DEFAULT_GLOBAL_FORMAT = "%4l %h%p%t %R"
global_format = os.getenv("PYSEQ_GLOBAL_FORMAT", DEFAULT_GLOBAL_FORMAT)

# use strict padding on sequences (pad length must match)
PYSEQ_STRICT_PAD = os.getenv("PYSEQ_STRICT_PAD", 0)
PYSEQ_NOT_STRICT = os.getenv("PYSEQ_NOT_STRICT", 1)
strict_pad = int(PYSEQ_STRICT_PAD) == 1 or int(PYSEQ_NOT_STRICT) == 0

# regex pattern for matching frame numbers only
# pyseq intentionally stays permissive here and lets sibling/diff logic decide
# whether matching numeric tokens represent the sequence frame component.
DEFAULT_FRAME_PATTERN = r"\d+"
DEFAULT_SIGNED_FRAME_PATTERN = r"(?:(?<=^)|(?<=[._]))-\d+|\d+"

# regex pattern for matching all numeric sequence tokens in a filename
digits_re = re.compile(DEFAULT_FRAME_PATTERN)
PYSEQ_FRAME_PATTERN = os.getenv("PYSEQ_FRAME_PATTERN", DEFAULT_FRAME_PATTERN)
PYSEQ_ALLOW_NEGATIVE_FRAMES = os.getenv("PYSEQ_ALLOW_NEGATIVE_FRAMES", "0")

# regex patterns for explicit frame-range syntax parsing/formatting
DEFAULT_FRAME_RANGE_SEGMENT_PATTERN = (
    r"^\s*(?P<start>-?\d+)(?:\s*-\s*(?P<end>-?\d+)(?:\s*x\s*(?P<step>\d+))?)?\s*$"
)
DEFAULT_FRAME_RANGE_TEXT_PATTERN = (
    r"-?\d+(?:\s*-\s*-?\d+(?:\s*x\s*\d+)?)?(?:\s*,\s*-?\d+(?:\s*-\s*-?\d+(?:\s*x\s*\d+)?)?)*"
)
DEFAULT_SERIALIZED_RANGE_PATTERN = rf"\[[^\]]+\]|\s+(?:{DEFAULT_FRAME_RANGE_TEXT_PATTERN})\s*$"
DEFAULT_EMBEDDED_RANGE_PATTERN = rf"^(?P<head>.+?)(?P<range>\[(?:[^\]]+)\]|{DEFAULT_FRAME_RANGE_TEXT_PATTERN})(?P<tail>\.[^/\s]+)$"


def allow_negative_frames() -> bool:
    """Return True when explicit negative frame syntax is enabled."""
    return os.getenv("PYSEQ_ALLOW_NEGATIVE_FRAMES", PYSEQ_ALLOW_NEGATIVE_FRAMES) == "1"


def get_effective_frame_pattern(pattern: str = DEFAULT_FRAME_PATTERN) -> str:
    """Return the configured frame pattern, promoting the default when needed."""
    if allow_negative_frames() and pattern == DEFAULT_FRAME_PATTERN:
        return DEFAULT_SIGNED_FRAME_PATTERN
    return pattern


def set_frame_pattern(pattern: str = DEFAULT_FRAME_PATTERN):
    """
    Set the regex pattern for matching frame numbers.

    :param pattern: The regex pattern to use for matching frame numbers.
    """
    global frames_re
    global digits_re
    global PYSEQ_FRAME_PATTERN
    PYSEQ_FRAME_PATTERN = pattern
    try:
        compiled = re.compile(get_effective_frame_pattern(pattern))
        frames_re = compiled
        digits_re = compiled
    except Exception as e:
        print("Error: Invalid regex pattern: %s" % e)
        fallback = re.compile(DEFAULT_FRAME_PATTERN)
        frames_re = fallback
        digits_re = fallback


# set the default frame pattern
set_frame_pattern(PYSEQ_FRAME_PATTERN)

# regex for matching format directives
format_re = re.compile(r"%(?P<pad>\d+)?(?P<var>\w+)")

# character to join explicit frame ranges on
DEFAULT_RANGE_SEP = ", "
range_join = os.getenv("PYSEQ_RANGE_SEP", DEFAULT_RANGE_SEP)
