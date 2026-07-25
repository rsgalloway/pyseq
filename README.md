![pyseq logo](docs/assets/logo.png)

# PySeq

[![PyPI](https://img.shields.io/pypi/v/pyseq.svg)](https://pypi.org/project/pyseq/)
[![CI](https://github.com/rsgalloway/pyseq/actions/workflows/tests.yml/badge.svg)](https://github.com/rsgalloway/pyseq/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

PySeq is a Python library for detecting, parsing, and formatting numbered file
sequences such as `fileA.0001.png`, `fileA.0002.png`, and
`fileA.0003.png`. It groups matching filenames into a compact sequence form
like `fileA.1-3.png`, regardless of where the frame number appears in the
name.

Used in visual effects, animation, and post-production pipelines.

[Installation](#installation) |
[Quick Examples](#quick-examples) |
[Production Usage](#production-usage) |
[Command-Line Tools](#command-line-tools) |
[Docs](#docs) |
[Contributing](#contributing) |
[Testing](#testing)

## Installation

The easiest way to install pyseq:

```bash
$ pip install -U pyseq
```

OS packages are also available for some distributions:

- Ubuntu 26.04 LTS (`resolute`) from `universe`:

```bash
sudo apt install python3-pyseq
```

- Debian unstable (`sid`) as [`python3-pyseq`](https://packages.debian.org/sid/python/python3-pyseq):

```bash
sudo apt install python3-pyseq
```

For environment configuration and source distribution setup, see
[Setup and Distribution](docs/setup-and-distribution.md).

## Quick Examples

Find grouped sequences from Python:

```python
>>> import pyseq
>>> seqs = pyseq.get_sequences("tests/files/*.png")
>>> print(seqs[0].format("%04l %h%p%t %R"))
0010 012_vb_110_v001.%04d.png [1-10]
```

Compress a list of filenames into a sequence:

```python
>>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
>>> print(s)
file.1-3.jpg
>>> s.append('file.0006.jpg')
>>> print(s.format("%h%p%t %R"))
file.%04d.jpg [1-3, 6]
```

Find grouped sequences from the command line:

```bash
$ lss tests/files/z1*
   4 z1_001_v1.%d.png [1-4]
   4 z1_002_v1.%d.png [1-4]
   4 z1_002_v2.%d.png [9-12]
```

Deserialize a compressed sequence string:

```python
>>> s = uncompress('./tests/012_vb_110_v001.%04d.png 1-1001', fmt='%h%p%t %r')
>>> len(s)
1001
>>> print(s.format('%04l %h%p%t %R'))
1001 012_vb_110_v001.%04d.png [1-1001]
```

Extended serialized range syntax is also supported for uncompression and
sequence reference parsing:

```python
>>> s = uncompress('render.%04d.exr 1001-1010x3', fmt='%h%p%t %x')
>>> print(s.frames())
[1001, 1004, 1007, 1010]
>>> print(s.format('%h%p%t %x'))
render.%04d.exr 1001-1010x3
```

Supported serialized range forms include:

- `1001-1100`
- `1001-1100x2`
- `1001-1100x10, 1200, 1300-1320x5`
- `10-1x3`
- `-10--1x3` with `PYSEQ_ALLOW_NEGATIVE_FRAMES=1`

Negative frame ranges are opt-in so the default filename discovery path stays
fast and unopinionated. Enable them with:

```bash
export PYSEQ_ALLOW_NEGATIVE_FRAMES=1
```

## Production Usage

pyseq has been used for many years in production visual effects and animation
pipelines for parsing and manipulating image sequences. If your studio uses
pyseq, we'd love to hear from you.

## Command-Line Tools

PySeq comes with the following sequence-aware command-line tools:

| Command | Description                           | Example Usage                    |
| ------- | ------------------------------------- | -------------------------------- |
| `lss`   | List image sequences in a directory   | `lss shots/`                     |
| `stree` | Display sequence-aware directory tree | `stree shots/`                   |
| `sfind` | Recursively find image sequences      | `sfind assets/ -name "*.exr"`   |
| `sdiff` | Compare two sequences                 | `sdiff A.%04d.exr B.%04d.exr`    |
| `sstat` | Print detailed stats about a sequence | `sstat render.%04d.exr`          |
| `scopy` | Copy a sequence to another directory  | `scopy a.%04d.exr /tmp/output/`  |
| `srm`   | Remove a sequence or frame range      | `srm a.1001-1100.exr`            |
| `smv`   | Move or rename a sequence             | `smv b.%04d.exr /tmp/archive/` |

## Docs

Additional documentation is available in the [docs](docs/) folder:

- [Docs Overview](docs/README.md)
- [Examples](docs/examples.md)
- [CLI Tools Reference](docs/cli-tools.md)
- [Setup and Distribution](docs/setup-and-distribution.md)
- [Formatting Reference](docs/formatting.md)
- [Frame Patterns](docs/frame-patterns.md)

## Contributing

Contributor guidance lives in [CONTRIBUTING.md](CONTRIBUTING.md).

## Testing

To run the unit tests, simply run `pytest` in a shell:

```bash
$ pytest tests -q
```
