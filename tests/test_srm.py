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
Contains tests for the srm CLI and sremove module.
"""

import os
import subprocess
import tempfile
import pytest

import pyseq
from conftest import get_installed_command
from pyseq.sremove import remove_sequence

srm_bin = get_installed_command("srm")


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


def test_remove_sequence_basic(sample_sequence):
    """Test removing a sequence of files."""
    src_dir, seq = sample_sequence
    remove_sequence(
        seq=seq,
        src_dir=src_dir,
        force=False,
        dryrun=False,
        verbose=False,
    )

    for i in range(1, 4):
        old_path = os.path.join(src_dir, f"test.{i:04d}.exr")
        assert not os.path.exists(old_path)


def test_srm_cli(sample_sequence):
    """Test the command-line interface of srm."""
    src_dir, _ = sample_sequence
    pattern = os.path.join(src_dir, "test.%04d.exr")

    result = subprocess.run(
        [srm_bin, pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for i in range(1, 4):
        old_path = os.path.join(src_dir, f"test.{i:04d}.exr")
        assert not os.path.exists(old_path)


def test_srm_cli_dryrun(sample_sequence):
    """Dry-run should print planned removals without deleting files."""
    src_dir, _ = sample_sequence
    pattern = os.path.join(src_dir, "test.%04d.exr")

    result = subprocess.run(
        [srm_bin, pattern, "--dryrun"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "test.0001.exr" in result.stdout
    for i in range(1, 4):
        assert os.path.exists(os.path.join(src_dir, f"test.{i:04d}.exr"))


def test_srm_cli_explicit_sequence_string(tmp_path):
    """Serialized sequence strings should resolve before removal."""
    for i in range(1, 6):
        (tmp_path / f"shot.{i:04d}.exr").write_text("dummy frame")

    src = str(tmp_path / "shot.%04d.exr") + " 2-4"

    result = subprocess.run(
        [srm_bin, src],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert os.path.exists(tmp_path / "shot.0001.exr")
    assert os.path.exists(tmp_path / "shot.0005.exr")
    for i in range(2, 5):
        assert not os.path.exists(tmp_path / f"shot.{i:04d}.exr")


def test_srm_cli_embedded_range(tmp_path):
    """Embedded range syntax should resolve against on-disk padded sequences."""
    for i in range(1, 6):
        (tmp_path / f"plate.{i:04d}.rgb").write_text("dummy frame")

    result = subprocess.run(
        [srm_bin, str(tmp_path / "plate.2-4.rgb")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert os.path.exists(tmp_path / "plate.0001.rgb")
    assert os.path.exists(tmp_path / "plate.0005.rgb")
    for i in range(2, 5):
        assert not os.path.exists(tmp_path / f"plate.{i:04d}.rgb")
