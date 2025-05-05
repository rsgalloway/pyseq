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
Contains tests for the sfind module.
"""

import os
import subprocess
import tempfile
import pytest


@pytest.fixture
def nested_sequence_tree():
    """Create a temporary directory with a nested sequence tree for testing."""
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "subdir1"))
        os.makedirs(os.path.join(root, "subdir2"))

        for i in range(1, 4):
            with open(os.path.join(root, f"shotA.{i:04d}.exr"), "w") as f:
                f.write("A")
            with open(os.path.join(root, "subdir1", f"shotB.{i:04d}.png"), "w") as f:
                f.write("B")
            with open(os.path.join(root, "subdir2", f"notes_{i}.txt"), "w") as f:
                f.write("notes")

        yield root


def test_sfind_basic(nested_sequence_tree):
    """Test sfind with no arguments to find all files."""
    result = subprocess.run(
        ["sfind", nested_sequence_tree],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout
    assert "shotA.1-3.exr" in out
    assert "shotB.1-3.png" in out


def test_sfind_filter(nested_sequence_tree):
    """Test sfind with a filter to only find PNG files."""
    result = subprocess.run(
        ["sfind", nested_sequence_tree, "-name", "*.png"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout
    assert "shotB.1-3.png" in out
    assert "shotA" not in out
