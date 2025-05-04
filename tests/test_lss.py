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
Contains tests for the lss module.
"""

import os
import subprocess
import tempfile
import pytest


@pytest.fixture
def lss_fixture():
    """Fixture to create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1, 4):
            with open(os.path.join(tmpdir, f"shot.{i:04d}.exr"), "w") as f:
                f.write("frame\n")
        yield tmpdir


def test_lss_with_directory(lss_fixture):
    """Test lss with a directory input."""
    result = subprocess.run(
        ["lss", lss_fixture],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout
    assert "   3 shot.%04d.exr [1-3]" in out


def test_lss_with_wildcard(lss_fixture):
    """Test lss with a wildcard pattern."""
    pattern = os.path.join(lss_fixture, "shot.*.exr")

    result = subprocess.run(
        ["lss", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout
    assert "   3 shot.%04d.exr [1-3]" in out


def test_lss_stdin_input(lss_fixture):
    """Test lss with stdin input."""
    result = subprocess.run(
        ["lss"],
        input=f"{lss_fixture}\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout
    assert "   3 shot.%04d.exr [1-3]" in out
