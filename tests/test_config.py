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
#

__doc__ = """
Contains tests for the config module.
"""

import re
from pyseq.config import set_frame_pattern, frames_re, DEFAULT_FRAME_PATTERN


def test_set_frame_pattern_valid():
    """Test that a valid regex pattern is set correctly"""
    pattern = r"\d+"
    set_frame_pattern(pattern)
    assert frames_re.pattern == pattern
    assert isinstance(frames_re, re.Pattern)


def test_set_frame_pattern_invalid():
    """Test that invalid regex pattern falls back to default pattern"""
    # intentionally broken regex
    bad_pattern = r"("
    set_frame_pattern(bad_pattern)
    # expect fallback to default
    assert frames_re.pattern == DEFAULT_FRAME_PATTERN


def test_set_frame_pattern_invalid_prints_error(capfd):
    """Test that invalid regex prints an error and reverts to default pattern"""
    bad_pattern = r"["
    set_frame_pattern(bad_pattern)
    out, err = capfd.readouterr()
    assert "Error: Invalid regex pattern" in out
    assert frames_re.pattern == DEFAULT_FRAME_PATTERN
