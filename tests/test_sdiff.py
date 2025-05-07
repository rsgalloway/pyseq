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
Contains tests for the sdiff module.
"""

import json
import os
import subprocess
import tempfile
import pytest

import pyseq
from pyseq.sdiff import diff_sequences

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if os.name == "nt":
    sdiff_bin = os.path.join(project_root, "bin", "sdiff.bat")
else:
    sdiff_bin = os.path.join(project_root, "bin", "sdiff")


@pytest.fixture
def diff_test_sequences():
    """Create two temporary directories with different sequences for testing."""
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        # create: foo.0001-0003.exr
        for i in range(1, 4):
            path = os.path.join(dir1, f"foo.{i:04d}.exr")
            with open(path, "wb") as f:
                f.write(b"dummy A\n")

        # create: bar.0001-0002.exr (diff head + 1 missing frame)
        for i in range(1, 3):
            path = os.path.join(dir2, f"bar.{i:04d}.exr")
            with open(path, "wb") as f:
                f.write(b"dummy B\n")

        seq1 = pyseq.get_sequences(os.listdir(dir1))[0]
        seq2 = pyseq.get_sequences(os.listdir(dir2))[0]
        yield dir1, seq1, dir2, seq2


def test_diff_sequences(diff_test_sequences):
    """Test the diff_sequences function."""
    _, seq1, _, seq2 = diff_test_sequences
    diff = diff_sequences(seq1, seq2)

    assert diff["head"][0] != diff["head"][1]
    assert diff["length"][0] == 3
    assert diff["length"][1] == 2
    # assert 3 in diff["missing"]["b_only"]


def test_sdiff_cli_text(diff_test_sequences):
    """Test the sdiff CLI with text output."""
    dir1, _, dir2, _ = diff_test_sequences
    pattern1 = os.path.join(dir1, "foo.%04d.exr")
    pattern2 = os.path.join(dir2, "bar.%04d.exr")

    result = subprocess.run(
        [sdiff_bin, pattern1, pattern2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    assert "Head mismatch" in result.stdout
    assert "Length mismatch" in result.stdout


def test_sdiff_cli_json(diff_test_sequences):
    """Test the sdiff CLI with JSON output."""
    dir1, _, dir2, _ = diff_test_sequences
    pattern1 = os.path.join(dir1, "foo.%04d.exr")
    pattern2 = os.path.join(dir2, "bar.%04d.exr")

    result = subprocess.run(
        [sdiff_bin, "--json", pattern1, pattern2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["head"][0].startswith("foo")
    assert data["head"][1].startswith("bar")
    assert data["length"] == [3, 2]
