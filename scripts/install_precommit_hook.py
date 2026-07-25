#!/usr/bin/env python3
#
# Copyright (c) 2011-2026, Ryan Galloway (ryan@rsgalloway.com)
#

"""Install an optional git pre-commit hook for local quality checks."""

import stat
import sys
from pathlib import Path

HOOK_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail

ROOT={root}
PYTHON={python}

cd "$ROOT"

"$PYTHON" -m isort --check-only --diff lib/pyseq tests scripts
"$PYTHON" -m black --check lib/pyseq tests scripts
"$PYTHON" -m flake8 lib/pyseq tests scripts
"$PYTHON" -m pytest tests -q
"""


def main():
    repo_root = Path(__file__).resolve().parent.parent
    git_dir = repo_root / ".git"
    hooks_dir = git_dir / "hooks"
    hook_path = hooks_dir / "pre-commit"

    if not git_dir.exists():
        raise SystemExit("No .git directory found; run this from a git checkout.")

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(
        HOOK_TEMPLATE.format(
            root=repr(str(repo_root)),
            python=repr(sys.executable),
        ),
        encoding="utf-8",
    )
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Installed pre-commit hook at {hook_path}")


if __name__ == "__main__":
    main()
