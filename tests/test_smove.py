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
Contains tests for the smv console command and smove module.
"""

import os
import subprocess
import tempfile
import pytest

import pyseq
from conftest import get_installed_command
from pyseq.smove import move_sequence

smv_bin = get_installed_command("smv")


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


def test_smv_cli(sample_sequence):
    """Test the command-line interface of smv."""
    src_dir, _ = sample_sequence
    with tempfile.TemporaryDirectory() as dest_dir:
        pattern = os.path.join(src_dir, "test.%04d.exr")

        result = subprocess.run(
            [smv_bin, pattern, dest_dir],
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


def test_smv_cli_rename_sequence_pattern(sample_sequence):
    """smv should support mv-style sequence renames."""
    src_dir, _ = sample_sequence
    src_pattern = os.path.join(src_dir, "test.%04d.exr")
    dest_pattern = os.path.join(src_dir, "renamed.%04d.exr")

    result = subprocess.run(
        [smv_bin, src_pattern, dest_pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for i in range(1, 4):
        assert os.path.exists(os.path.join(src_dir, f"renamed.{i:04d}.exr"))
        assert not os.path.exists(os.path.join(src_dir, f"test.{i:04d}.exr"))


def test_smv_cli_creates_destination_directory(sample_sequence):
    """smv should create a destination directory when moving a sequence."""
    src_dir, _ = sample_sequence
    parent_dir = tempfile.mkdtemp()
    try:
        dest_dir = os.path.join(parent_dir, "archive")
        pattern = os.path.join(src_dir, "test.%04d.exr")

        result = subprocess.run(
            [smv_bin, pattern, dest_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        for i in range(1, 4):
            assert os.path.exists(os.path.join(dest_dir, f"test.{i:04d}.exr"))
            assert not os.path.exists(os.path.join(src_dir, f"test.{i:04d}.exr"))
    finally:
        for root, dirs, files in os.walk(parent_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(parent_dir)


def test_smv_cli_wildcard_source(sample_sequence):
    """Wildcard sources should resolve to a sequence before moving."""
    src_dir, _ = sample_sequence
    dest_dir = tempfile.mkdtemp()
    try:
        wildcard = os.path.join(src_dir, "test.*.exr")

        result = subprocess.run(
            [smv_bin, wildcard, dest_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        for i in range(1, 4):
            assert os.path.exists(os.path.join(dest_dir, f"test.{i:04d}.exr"))
    finally:
        for root, dirs, files in os.walk(dest_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(dest_dir)


def test_smv_cli_multiple_sources_require_directory(tmp_path):
    """Multiple sources should require a destination directory."""
    for prefix in ("a", "b"):
        for i in range(1, 3):
            (tmp_path / f"{prefix}.{i:04d}.exr").write_text("dummy frame")

    src_a = str(tmp_path / "a.%04d.exr")
    src_b = str(tmp_path / "b.%04d.exr")
    dest_pattern = str(tmp_path / "renamed.%04d.exr")

    result = subprocess.run(
        [smv_bin, src_a, src_b, dest_pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 1
    assert "destination must be a directory" in result.stderr


def test_smv_cli_explicit_sequence_string_source_and_dest(tmp_path):
    """Serialized sequence strings should resolve before moving."""
    for i in range(1, 6):
        (tmp_path / f"shot.{i:04d}.exr").write_text("dummy frame")

    src = str(tmp_path / "shot.%04d.exr") + " 1-3"
    dest = str(tmp_path / "take.%04d.exr") + " 1001-1003"

    result = subprocess.run(
        [smv_bin, src, dest],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for i in range(1001, 1004):
        assert os.path.exists(tmp_path / f"take.{i:04d}.exr")
    for i in range(1, 4):
        assert not os.path.exists(tmp_path / f"shot.{i:04d}.exr")
    for i in range(4, 6):
        assert os.path.exists(tmp_path / f"shot.{i:04d}.exr")


def test_smv_cli_embedded_range_source_and_dest(tmp_path):
    """Embedded range syntax should resolve against on-disk padded sequences."""
    for i in range(1, 6):
        (tmp_path / f"plate.{i:04d}.rgb").write_text("dummy frame")

    src = str(tmp_path / "plate.2-4.rgb")
    dest = str(tmp_path / "beauty.20-22.rgb")

    result = subprocess.run(
        [smv_bin, src, dest],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for i in range(20, 23):
        assert os.path.exists(tmp_path / f"beauty.{i:04d}.rgb")
    assert os.path.exists(tmp_path / "plate.0001.rgb")
    assert os.path.exists(tmp_path / "plate.0005.rgb")
    for i in range(2, 5):
        assert not os.path.exists(tmp_path / f"plate.{i:04d}.rgb")
