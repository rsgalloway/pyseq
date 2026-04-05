#!/usr/bin/env python

import os

import pytest

from pyseq import lss, scopy, sdiff, sfind, smove, sstat, stree


def _raise_keyboard_interrupt(*args, **kwargs):
    raise KeyboardInterrupt()


@pytest.mark.parametrize(
    ("module", "argv", "patch_target"),
    [
        (lss, ["lss", "."], "get_sequences"),
        (sfind, ["sfind", "."], "walk_and_collect_sequences"),
        (stree, ["stree"], "print_tree"),
        (sdiff, ["sdiff", "a.%04d.exr", "b.%04d.exr"], "resolve_sequence"),
        (sstat, ["sstat", "a.%04d.exr"], "resolve_sequence"),
    ],
)
def test_cli_main_handles_keyboard_interrupt(
    monkeypatch, capsys, tmp_path, module, argv, patch_target
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, patch_target, _raise_keyboard_interrupt)
    monkeypatch.setattr("sys.argv", argv)

    assert module.main() == 1
    captured = capsys.readouterr()
    assert "stopping..." in captured.err


@pytest.mark.parametrize(("module", "command"), [(scopy, "scopy"), (smove, "smove")])
def test_copy_move_cli_main_handles_keyboard_interrupt(
    monkeypatch, capsys, tmp_path, module, command
):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    monkeypatch.setattr(module, "resolve_sequence", _raise_keyboard_interrupt)
    monkeypatch.setattr("sys.argv", [command, "a.%04d.exr", str(dest_dir)])

    assert module.main() == 1
    captured = capsys.readouterr()
    assert "stopping..." in captured.err
