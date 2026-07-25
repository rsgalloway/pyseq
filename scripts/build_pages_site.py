#!/usr/bin/env python3
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Build a simple Jekyll-friendly docs site from repository markdown files."""

import argparse
import re
import shutil
from pathlib import Path
from typing import Optional

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
markdown: kramdown
permalink: pretty
"""
    (output_dir / "_config.yml").write_text(config, encoding="utf-8")


def write_layout(output_dir: Path):
    """Write the shared Jekyll layout used by the generated docs site."""
    layout_dir = output_dir / "_layouts"
    layout_dir.mkdir(parents=True, exist_ok=True)
    template = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% if page.title %}{{ page.title }} | {% endif %}{{ site.title }}</title>
    <meta name="description" content="{{ site.description }}">
    <link rel="stylesheet" href="{{ '/assets/site.css' | relative_url }}">
  </head>
  <body>
    <div class="site-shell">
      <header class="site-header">
        <a class="site-brand" href="{{ '/' | relative_url }}">{{ site.title }}</a>
        <nav class="site-nav">
          <a href="{{ '/' | relative_url }}">Home</a>
          <a href="{{ '/docs/cli-tools/' | relative_url }}">CLI Tools</a>
          <a href="{{ '/docs/examples/' | relative_url }}">Examples</a>
          <a href="{{ '/docs/formatting/' | relative_url }}">Formatting</a>
          <a href="{{ '/docs/frame-patterns/' | relative_url }}">Frame Patterns</a>
          <a href="{{ '/docs/performance/' | relative_url }}">Performance</a>
          <a href="{{ '/docs/setup-and-distribution/' | relative_url }}">Setup</a>
          <a href="https://github.com/rsgalloway/pyseq">GitHub</a>
          <a href="https://pypi.org/project/pyseq/">PyPI</a>
        </nav>
      </header>
      <main class="site-main">
        {{ content }}
      </main>
    </div>
  </body>
</html>
"""
    (layout_dir / "default.html").write_text(template, encoding="utf-8")


def write_stylesheet(output_dir: Path):
    """Write a minimal light stylesheet for the generated docs site."""
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css = """:root {
  --bg: #f7fafc;
  --panel: #ffffff;
  --border: #d9e2ec;
  --text: #102033;
  --muted: #516172;
  --accent: #0fba74;
  --accent-dark: #0b7f55;
  --code: #f3f6f9;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background:
    radial-gradient(circle at top, rgba(15,186,116,0.08), transparent 32%),
    linear-gradient(180deg, #fcfefe 0%, #f4f8fb 100%);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.7;
}

a {
  color: var(--accent-dark);
  text-decoration: none;
}

a:hover {
  color: var(--accent);
}

.site-shell {
  max-width: 1040px;
  margin: 0 auto;
  padding: 24px 24px 72px;
}

.site-header {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
}

.site-brand {
  color: var(--text);
  font-size: 0.98rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.site-nav a {
  color: var(--muted);
  font-size: 0.95rem;
}

.site-nav a:hover {
  color: var(--text);
}

.site-main {
  background: transparent;
}

.site-main h1:first-child,
.site-main p:first-child img {
  margin-top: 0;
}

h1, h2, h3 {
  color: var(--text);
  line-height: 1.15;
}

h1 {
  font-size: 2.7rem;
  margin: 0 0 1rem;
}

h2 {
  font-size: 1.5rem;
  margin-top: 2.5rem;
}

h3 {
  font-size: 1.08rem;
  margin-top: 1.5rem;
}

p, li {
  font-size: 1.02rem;
}

code, pre {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

code {
  background: var(--code);
  border: 1px solid #e4ebf2;
  border-radius: 8px;
  padding: 0.12rem 0.4rem;
}

pre {
  background: #f8fbfd;
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow-x: auto;
  padding: 18px 20px;
}

pre code {
  background: transparent;
  border: 0;
  padding: 0;
}

img {
  max-width: 100%;
  height: auto;
}

blockquote {
  border-left: 4px solid #b8c6d6;
  color: var(--muted);
  margin: 1.5rem 0;
  padding-left: 1rem;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border: 1px solid var(--border);
  padding: 0.7rem 0.8rem;
  text-align: left;
}

th {
  background: #f2f6fa;
}

@media (max-width: 720px) {
  .site-shell {
    padding: 18px 16px 56px;
  }

  .site-header {
    align-items: flex-start;
    margin-bottom: 28px;
  }

  .site-nav {
    gap: 12px;
  }

  h1 {
    font-size: 2.15rem;
  }
}
"""
    (assets_dir / "site.css").write_text(css, encoding="utf-8")


def append_benchmark_section(
    content: str,
    benchmark_summary: Optional[Path] = None,
    benchmark_json: Optional[Path] = None,
) -> str:
    """Append the latest benchmark summary to the performance document."""
    sections = [content.rstrip(), "", "## Latest Benchmarks", ""]

    if benchmark_summary and benchmark_summary.exists():
        sections.extend(
            [
                "This section is generated automatically by the docs publishing workflow,",
                "which runs `scripts/benchmark.py` on the current `master` branch before",
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


def copy_docs_assets(docs_dir: Path, output_dir: Path):
    """Copy docs assets to both root assets/ and docs/assets/ for relative links."""
    assets_src = docs_dir / "assets"
    if not assets_src.exists():
        return

    root_assets = output_dir / "assets"
    docs_assets = output_dir / "docs" / "assets"
    root_assets.mkdir(parents=True, exist_ok=True)
    docs_assets.mkdir(parents=True, exist_ok=True)

    for src in assets_src.iterdir():
        if src.is_file():
            shutil.copy2(src, root_assets / src.name)
            shutil.copy2(src, docs_assets / src.name)


def build_site(args):
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output).resolve()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_site_config(output_dir)
    write_layout(output_dir)
    write_stylesheet(output_dir)

    # Home page from docs/index.md.
    write_markdown_page(repo_root / "docs" / "index.md", output_dir / "index.md", "pyseq")

    benchmark_summary = Path(args.benchmark_summary) if args.benchmark_summary else None
    benchmark_json = Path(args.benchmark_json) if args.benchmark_json else None

    # Docs pages.
    docs_dir = repo_root / "docs"
    for src in docs_dir.glob("*.md"):
        if src.name == "index.md":
            continue
        if src.name == "README.md":
            dst = output_dir / "docs" / "index.md"
            fallback = "Docs"
        else:
            dst = output_dir / "docs" / src.name
            fallback = src.stem.replace("-", " ").title()
        if src.name == "performance.md":
            content = src.read_text(encoding="utf-8")
            content = append_benchmark_section(content, benchmark_summary, benchmark_json)
            content = rewrite_links(content)
            title = extract_title(content, fallback)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(wrap_markdown(content, title), encoding="utf-8")
        else:
            write_markdown_page(src, dst, fallback)

    copy_docs_assets(docs_dir, output_dir)

    if benchmark_json and benchmark_json.exists():
        shutil.copy2(benchmark_json, output_dir / "assets" / "benchmark.json")

    cname = repo_root / "CNAME"
    if cname.exists():
        shutil.copy2(cname, output_dir / "CNAME")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark-summary")
    parser.add_argument("--benchmark-json")
    args = parser.parse_args()
    build_site(args)


if __name__ == "__main__":
    main()
