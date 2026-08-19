#!/usr/bin/env python3
#
# Copyright (c) 2011-2026, Ryan Galloway (ryan@rsgalloway.com)
#

"""Stage repository docs into the layout expected by the mkpages Pages build."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Optional


def copy_text(src: Path, dst: Path) -> None:
    """Copy one text file, creating parent directories as needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def copy_tree(src: Path, dst: Path) -> None:
    """Copy one directory tree if it exists."""
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def append_benchmark_section(
    content: str,
    benchmark_summary: Optional[Path] = None,
    benchmark_json: Optional[Path] = None,
) -> str:
    """Append the latest benchmark summary to the performance guide."""
    sections = [content.rstrip(), "", "## Latest Benchmarks", ""]

    if benchmark_summary and benchmark_summary.exists():
        sections.extend(
            [
                "This section is generated automatically by the docs publishing workflow,",
                "which runs `scripts/benchmark.py` for the current workflow ref before",
                "building the Pages site.",
                "",
                benchmark_summary.read_text(encoding="utf-8").strip(),
                "",
            ]
        )
    else:
        sections.extend(
            [
                "This section is generated automatically by the docs publishing workflow",
                "when benchmark artifacts are available.",
                "",
            ]
        )

    if benchmark_json and benchmark_json.exists():
        sections.extend(["### Downloads", "", "- [Benchmark JSON](../assets/benchmark.json)", ""])

    return "\n".join(sections).rstrip() + "\n"


def stage_site(
    repo_root: Path,
    output_dir: Path,
    benchmark_summary: Optional[Path] = None,
    benchmark_json: Optional[Path] = None,
) -> None:
    """Arrange docs so mkpages can preserve the existing published URLs."""
    docs_dir = repo_root / "docs"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_text(docs_dir / "mkpages.yml", output_dir / "mkpages.yml")
    copy_text(repo_root / "README.md", output_dir / "README.md")
    copy_text(docs_dir / "index.md", output_dir / "index.md")
    copy_text(docs_dir / "README.md", output_dir / "docs" / "index.md")

    for src in docs_dir.glob("*.md"):
        if src.name in {"index.md", "README.md"}:
            continue
        dst = output_dir / "docs" / src.name
        if src.name == "performance.md":
            content = append_benchmark_section(
                src.read_text(encoding="utf-8"),
                benchmark_summary=benchmark_summary,
                benchmark_json=benchmark_json,
            )
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            continue
        copy_text(src, dst)

    copy_tree(docs_dir / "assets", output_dir / "assets")
    copy_tree(docs_dir / "assets", output_dir / "docs" / "assets")

    if benchmark_json and benchmark_json.exists():
        copy_text(benchmark_json, output_dir / "assets" / "benchmark.json")
        copy_text(benchmark_json, output_dir / "docs" / "assets" / "benchmark.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark-summary")
    parser.add_argument("--benchmark-json")
    args = parser.parse_args()
    stage_site(
        Path(args.repo_root).resolve(),
        Path(args.output).resolve(),
        benchmark_summary=(
            Path(args.benchmark_summary).resolve() if args.benchmark_summary else None
        ),
        benchmark_json=Path(args.benchmark_json).resolve() if args.benchmark_json else None,
    )


if __name__ == "__main__":
    main()
