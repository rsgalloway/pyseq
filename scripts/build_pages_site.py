#!/usr/bin/env python3
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Build a simple Jekyll-friendly docs site from repository markdown files."""

import argparse
import re
import shutil
from pathlib import Path


LINK_PATTERNS = (
    (r"\(README\.md\)", "(index.html)"),
    (r"\(docs/README\.md\)", "(docs/index.html)"),
    (r"\(docs/([^)]+)\.md\)", r"(docs/\1.html)"),
    (r"\(([^:)#]+)\.md\)", r"(\1.html)"),
)


def rewrite_links(content: str) -> str:
    """Rewrite local markdown links for generated HTML output."""
    updated = content
    for pattern, replacement in LINK_PATTERNS:
        updated = re.sub(pattern, replacement, updated)
    return updated


def extract_title(content: str, fallback: str) -> str:
    """Extract the first markdown H1 title or use a fallback."""
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def wrap_markdown(content: str, title: str) -> str:
    """Add minimal Jekyll front matter to markdown content."""
    return f"---\nlayout: default\ntitle: {title}\n---\n\n{content}"


def write_markdown_page(src: Path, dst: Path, fallback_title: str):
    """Copy a markdown file into the site tree with front matter and fixed links."""
    content = src.read_text(encoding="utf-8")
    title = extract_title(content, fallback_title)
    content = rewrite_links(content)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(wrap_markdown(content, title), encoding="utf-8")


def write_site_config(output_dir: Path):
    """Write a minimal Jekyll config file."""
    config = """title: pyseq
description: Python library for numbered file sequences
theme: minima
markdown: kramdown
permalink: pretty
"""
    (output_dir / "_config.yml").write_text(config, encoding="utf-8")


def write_benchmarks_page(
    output_dir: Path,
    core_summary: Path = None,
    cli_summary: Path = None,
    core_json: Path = None,
    cli_json: Path = None,
):
    """Create a latest benchmark report page and copy JSON artifacts."""
    benchmarks_dir = output_dir / "benchmarks"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)

    sections = [
        "# Latest Benchmarks",
        "",
        "This page is generated automatically from the benchmark workflows.",
        "",
    ]

    if core_summary and core_summary.exists():
        sections.extend([core_summary.read_text(encoding="utf-8").strip(), ""])

    if cli_summary and cli_summary.exists():
        sections.extend([cli_summary.read_text(encoding="utf-8").strip(), ""])

    downloads = []
    if core_json and core_json.exists():
        shutil.copy2(core_json, benchmarks_dir / "benchmark-core.json")
        downloads.append("- [Core benchmark JSON](benchmark-core.json)")
    if cli_json and cli_json.exists():
        shutil.copy2(cli_json, benchmarks_dir / "benchmark-cli.json")
        downloads.append("- [CLI benchmark JSON](benchmark-cli.json)")

    if downloads:
        sections.extend(["## Downloads", "", *downloads, ""])

    page = wrap_markdown("\n".join(sections).rstrip() + "\n", "Latest Benchmarks")
    (benchmarks_dir / "index.md").write_text(page, encoding="utf-8")


def build_site(args):
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output).resolve()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_site_config(output_dir)

    # Home page from the repository README.
    write_markdown_page(repo_root / "README.md", output_dir / "index.md", "pyseq")

    # Docs pages.
    docs_dir = repo_root / "docs"
    for src in docs_dir.glob("*.md"):
        if src.name == "README.md":
            dst = output_dir / "docs" / "index.md"
            fallback = "Docs"
        else:
            dst = output_dir / "docs" / src.name
            fallback = src.stem.replace("-", " ").title()
        write_markdown_page(src, dst, fallback)

    if (docs_dir / "assets").exists():
        shutil.copytree(docs_dir / "assets", output_dir / "docs" / "assets")

    cname = repo_root / "CNAME"
    if cname.exists():
        shutil.copy2(cname, output_dir / "CNAME")

    write_benchmarks_page(
        output_dir,
        core_summary=Path(args.core_summary) if args.core_summary else None,
        cli_summary=Path(args.cli_summary) if args.cli_summary else None,
        core_json=Path(args.core_json) if args.core_json else None,
        cli_json=Path(args.cli_json) if args.cli_json else None,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--core-summary")
    parser.add_argument("--cli-summary")
    parser.add_argument("--core-json")
    parser.add_argument("--cli-json")
    args = parser.parse_args()
    build_site(args)


if __name__ == "__main__":
    main()
