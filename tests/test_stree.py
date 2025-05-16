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
Contains tests for the stree module.
"""

import os
import subprocess
import tempfile
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if os.name == "nt":
    stree_bin = os.path.join(project_root, "bin", "stree.bat")
else:
    stree_bin = os.path.join(project_root, "bin", "stree")


@pytest.fixture
def tree_fixture():
    """Fixture to create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "subdir"))

        # create foo.1-3.exr in root
        for i in range(1, 4):
            with open(os.path.join(root, f"foo.{i:04d}.exr"), "w") as f:
                f.write("frame\n")

        # create bar.1-2.exr in subdir
        for i in range(1, 3):
            with open(os.path.join(root, "subdir", f"bar.{i:04d}.exr"), "w") as f:
                f.write("frame\n")

        yield root


def test_stree_output(tree_fixture):
    """Test stree output."""
    result = subprocess.run(
        [stree_bin, tree_fixture],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    out = result.stdout

    assert "foo.1-3.exr" in out
    assert "bar.1-2.exr" in out
    assert "subdir" in out
    assert "├──" in out or "└──" in out  # tree chars


def test_stree_default_path(tree_fixture):
    """Test stree with no path argument, should use cwd."""
    cwd = os.getcwd()
    try:
        os.chdir(tree_fixture)
        result = subprocess.run(
            [stree_bin],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert result.returncode == 0
        out = result.stdout
        assert "foo.1-3.exr" in out
        assert "subdir" in out
    finally:
        os.chdir(cwd)
