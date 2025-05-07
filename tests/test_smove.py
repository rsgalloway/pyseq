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
Contains tests for the smove module.
"""

import os
import subprocess
import tempfile
import pytest

import pyseq
from pyseq.smove import move_sequence

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if os.name == "nt":
    smove_bin = os.path.join(project_root, "bin", "smove.bat")
else:
    smove_bin = os.path.join(project_root, "bin", "smove")


@pytest.fixture
def sample_sequence():
    """Fixture to create a temporary directory with a sequence of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1, 4):
            path = os.path.join(tmpdir, f"test.{i:04d}.exr")
            with open(path, "w") as f:
                f.write("dummy frame")
        seq = pyseq.get_sequences(os.listdir(tmpdir))[0]
        yield tmpdir, seq


def test_move_sequence_basic(sample_sequence):
    """Test moving a sequence of files."""
    src_dir, seq = sample_sequence
    with tempfile.TemporaryDirectory() as dest_dir:
        move_sequence(
            seq=seq,
            src_dir=src_dir,
            dest_dir=dest_dir,
            rename=None,
            renumber=None,
            pad=None,
            force=False,
            dryrun=False,
            verbose=False,
        )

        # verify destination files exist
        for i in range(1, 4):
            new_path = os.path.join(dest_dir, f"test.{i:04d}.exr")
            assert os.path.exists(new_path)

        # verify original files are gone
        for i in range(1, 4):
            old_path = os.path.join(src_dir, f"test.{i:04d}.exr")
            assert not os.path.exists(old_path)


def test_smove_cli(sample_sequence):
    """Test the command-line interface of smove."""
    src_dir, _ = sample_sequence
    with tempfile.TemporaryDirectory() as dest_dir:
        pattern = os.path.join(src_dir, "test.%04d.exr")

        result = subprocess.run(
            [smove_bin, pattern, dest_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0
        for i in range(1, 4):
            new_path = os.path.join(dest_dir, f"test.{i:04d}.exr")
            assert os.path.exists(new_path)
            old_path = os.path.join(src_dir, f"test.{i:04d}.exr")
            assert not os.path.exists(old_path)
