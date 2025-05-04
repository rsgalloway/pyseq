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
Contains tests for the sstat module.
"""

import os
import subprocess
import tempfile
import json
import pytest

import pyseq
from pyseq.sstat import json_sstat


@pytest.fixture
def stat_sequence():
    """Fixture to create a temporary directory with a sequence of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1, 4):
            with open(os.path.join(tmpdir, f"shotA.{i:04d}.exr"), "w") as f:
                f.write("data")
        seq = pyseq.get_sequences(os.path.join(tmpdir, "*"))[0]
        yield tmpdir, seq


def test_json_sstat(stat_sequence):
    """Test the json_sstat function."""
    _, seq = stat_sequence
    result = json_sstat(seq)

    assert result["sequence"].startswith("shotA.")
    assert result["length"] == 3
    assert result["pad"] == 4
    assert result["start"] == 1
    assert result["end"] == 3
    assert result["missing"] == []
    assert "access" in result and "first" in result["access"]


def test_sstat_cli_output(stat_sequence):
    """Test the sstat CLI output."""
    tmpdir, _ = stat_sequence
    pattern = os.path.join(tmpdir, "shotA.%04d.exr")

    result = subprocess.run(
        ["sstat", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    assert "Sequence:" in result.stdout
    assert "Frames:" in result.stdout
    assert "Access:" in result.stdout


def test_sstat_cli_json(stat_sequence):
    """Test the sstat CLI JSON output."""
    tmpdir, _ = stat_sequence
    pattern = os.path.join(tmpdir, "shotA.%04d.exr")

    result = subprocess.run(
        ["sstat", "--json", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["sequence"].startswith("shotA.")
    assert data["length"] == 3
    assert "access" in data


def test_sstat_missing_file():
    """Test the sstat CLI with a missing file."""
    pattern = "not_a_real_file.%04d.exr"

    result = subprocess.run(
        ["sstat", pattern], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    assert result.returncode != 0
    assert "error" in result.stderr.lower()
    assert "not_a_real_file" in result.stderr
