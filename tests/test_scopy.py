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

import os
import subprocess
import tempfile
import pytest

import pyseq
from pyseq.scopy import copy_sequence


@pytest.fixture
def sample_sequence(tmp_path):
    """Create a dummy sequence: test.0001.exr through test.0003.exr"""
    filenames = []
    for i in range(1, 4):
        name = f"test.{i:04d}.exr"
        path = tmp_path / name
        path.write_text("dummy frame")
        filenames.append(str(path.name))  # just filenames
    seq = pyseq.get_sequences(filenames)[0]
    return tmp_path, seq


def test_copy_sequence_basic(sample_sequence):
    """Test the basic functionality of copy_sequence."""
    src_dir, seq = sample_sequence
    with tempfile.TemporaryDirectory() as destdir:
        copy_sequence(
            seq=seq,
            src_dir=str(src_dir),
            dest_dir=destdir,
            rename=None,
            renumber=None,
            pad=None,
            force=False,
            dryrun=False,
            verbose=False,
        )

        for i in range(1, 4):
            expected = os.path.join(destdir, f"test.{i:04d}.exr")
            assert os.path.exists(expected), f"Expected file not copied: {expected}"


def test_scopy_cli(sample_sequence):
    """Test the command line interface for scopy."""
    src_dir, _ = sample_sequence
    with tempfile.TemporaryDirectory() as destdir:
        pattern = os.path.join(str(src_dir), "test.%04d.exr")

        result = subprocess.run(
            ["scopy", pattern, destdir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        for i in range(1, 4):
            expected = os.path.join(destdir, f"test.{i:04d}.exr")
            assert os.path.exists(expected)
