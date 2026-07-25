<p align="left">
  <img src="assets/logo.png" alt="pyseq logo" width="640">
</p>

pyseq is a **Python library for detecting, parsing, and formatting numbered
file sequences** used in visual effects, animation, and post-production
pipelines.

It groups matching filenames into a compressed sequence string regardless of
where the frame number appears in the name.

```bash
lss tests/files/z1*

   4 z1_001_v1.%d.png [1-4]
   4 z1_002_v1.%d.png [1-4]
   4 z1_002_v2.%d.png [9-12]
```

## Why pyseq

pyseq is a lightweight Python library and CLI toolkit for discovering,
compressing, formatting, and manipulating image sequences.

### Detect

- Group sibling filenames into coherent sequences
- Keep frame matching unopinionated and filename-position agnostic
- Work with directories, glob patterns, or explicit file lists

### Format

- Render compact ranges like `1-100`
- Preserve padding with patterns like `%04d`
- Support stepped serialized ranges such as `1001-1100x5`

### Automate

- Inspect sequences from Python or the command line
- Copy, move, diff, remove, and summarize sequence data
- Integrate cleanly into studio scripts and pipeline tools

## Sequence Strings

pyseq compresses frame lists into readable sequence references:

```text
fileA.%04d.png [1-3]
render.%04d.exr 1001-1100x5
```

That makes it useful for tools that need compressed sequence strings without
hard-coding where the frame digits must appear in the filename.

It is intentionally small: fast sequence detection, compact formatting, and
simple interfaces that are easy to embed.

## Install

```bash
pip install -U pyseq
```

## Quickstart

List sequences in a directory:

```bash
lss tests/files
```

Example output:

```text
  10 012_vb_110_v001.%04d.png [1-10]
  10 012_vb_110_v002.%04d.png [1-10]
   7 a.%03d.tga [1-3, 10, 12-14]
   1 alpha.txt 
   5 bnc01_TinkSO_tx_0_ty_0.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_0_ty_1.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_1_ty_0.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_1_ty_1.%04d.tif [101-105]
   4 file.%02d.tif [1-2, 98-99]
   1 file.info.03.rgb 
   3 file01.%03d.j2k [1-2, 4]
   4 file01_%04d.rgb [40-43]
   4 file02_%04d.rgb [44-47]
   4 file%d.03.rgb [1-4]
   3 fileA.%04d.jpg [1-3]
   3 fileA.%04d.png [1-3]
   1 file_02.tif 
   2 negA.-%04d.exr [1-2]
   2 negA.%04d.exr [0-1]
   4 stepA.%d.exr [1001, 1004, 1007, 1010]
   4 z1_001_v1.%d.png [1-4]
   4 z1_002_v1.%d.png [1-4]
   4 z1_002_v2.%d.png [9-12]
```

Find sequences from Python:

```python
import pyseq

seqs = pyseq.get_sequences("tests/files/*.png")
print(seqs[0].format("%04l %h%p%t %R"))
```

Expected output:

```text
0010 012_vb_110_v001.%04d.png [1-10]
```

Parse a stepped range:

```python
seq = pyseq.uncompress("render.%04d.exr 1001-1010x3", fmt="%h%p%t %x")
print(seq.frames())
```

Expected output:

```text
[1001, 1004, 1007, 1010]
```

## Learn More

- [PySeq Docs](README.md): docs overview
- [Examples](examples.md): Python and CLI usage patterns
- [CLI Tools Reference](cli-tools.md): bundled sequence-aware utilities
- [Formatting Reference](formatting.md): supported format directives
- [Frame Patterns](frame-patterns.md): frame matching behavior and configuration
- [Performance](performance.md): benchmark workflow and regression checks
- [Setup and Distribution](setup-and-distribution.md): packaging and release notes
