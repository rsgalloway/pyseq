# Examples

This guide expands on the examples in the main [README](../README.md) and
shows a few common ways pyseq is used in production scripts and tools.

## Parse a List of Frames into a Sequence

```python
from pyseq import Sequence

frames = [
    "beauty.1001.exr",
    "beauty.1002.exr",
    "beauty.1003.exr",
]

seq = Sequence(frames)

print(seq)
print(seq.format("%h%p%t %R"))
```

Expected output:

```text
beauty.1001-1003.exr
beauty.%04d.exr [1001-1003]
```

## Scan a Directory for Sequences

```python
import pyseq

for seq in pyseq.get_sequences("tests/files/*.png"):
    print(seq.format("%04l %h%p%t %R"))
```

This is useful when you want to detect shot outputs, plate deliveries, or cache
frames and then hand the results off to downstream validation or publishing
tools.

## Walk a Tree of Render Outputs

```python
import pyseq

for root, dirs, seqs in pyseq.walk("tests"):
    for seq in seqs:
        print(root, seq.format("%h%r%t"))
```

This pattern works well for building reports over render directories, ingest
areas, and archival scans where sequence grouping is more helpful than
individual filenames.

## Detect Missing Frames

```python
from pyseq import Sequence

seq = Sequence(
    [
        "sim.1001.vdb",
        "sim.1002.vdb",
        "sim.1005.vdb",
    ]
)

print(seq.format("%h%p%t %M"))
```

Expected output:

```text
sim.%04d.vdb [1003-1004]
```

The `%M` formatter is especially useful for QC tools and publish validators
that need to flag broken frame ranges.

## Parse a Compressed Sequence String

```python
from pyseq import uncompress

seq = uncompress("comp.%04d.exr 1001-1005", fmt="%h%p%t %r")

print(len(seq))
print(seq[0])
print(seq[-1])
```

Expected output:

```text
5
comp.1001.exr
comp.1005.exr
```

## Parse a Stepped Sequence String

```python
from pyseq import uncompress

seq = uncompress("render.%04d.exr 1001-1010x3", fmt="%h%p%t %x")

print(seq.frames())
print(seq.format("%h%p%t %x"))
```

Expected output:

```text
[1001, 1004, 1007, 1010]
render.%04d.exr 1001-1010x3
```

## Parse Signed Serialized Frame Ranges

Signed frame ranges are opt-in. Enable them first:

```bash
export PYSEQ_ALLOW_NEGATIVE_FRAMES=1
```

Then serialized range strings may include signed frame numbers:

```python
from pyseq import uncompress

seq = uncompress("render.%04d.exr -10--1x3", fmt="%h%p%t %x")

print(seq.frames())
print(seq.format("%x"))
```

Expected output:

```text
[-10, -7, -4, -1]
-10--1x3
```

Signed frame ranges also work with on-disk filename patterns such as
`render.-0010.exr` when resolving or discovering sequences.

## Resolve a Sequence Pattern on Disk

`resolve_sequence` looks up files on disk from a compressed sequence pattern and
returns a `Sequence` object for the matching files.

```python
from pyseq.util import resolve_sequence

seq = resolve_sequence("tests/files/fileA.%04d.png")

print(seq)
print(seq.format("%h%p%t %R"))
```

Expected output:

```text
fileA.1-3.png
fileA.%04d.png [1-3]
```

This is handy when a tool stores a sequence pattern such as
`render.%04d.exr` and you want to recover the actual frames present on disk.

## Resolve a Variable-Width Sequence Pattern

When the pattern uses `%d`, `resolve_sequence` will match any digit width that
fits the rest of the filename.

```python
from pyseq.util import resolve_sequence

seq = resolve_sequence("tests/files/z1_002_v2.%d.png")

print(seq)
print(seq.format("%h%p%t %R"))
```

Expected output:

```text
z1_002_v2.9-12.png
z1_002_v2.%d.png [9-12]
```

## Handle Missing Matches

`resolve_sequence` raises `FileNotFoundError` when no files match the provided
pattern.

```python
from pyseq.util import resolve_sequence

try:
    resolve_sequence("tests/files/missing.%04d.exr")
except FileNotFoundError as exc:
    print(exc)
```

Expected output:

```text
No files match pattern: tests/files/missing.%04d.exr
```

## Format Sequences for Pipeline Output

```python
import pyseq

seq = pyseq.get_sequences("tests/files/fileA.*.png")[0]

print(seq.format("%l frames: %h%r%t"))
print(seq.format("%D%h%p%t %R"))
```

Example output:

```text
3 frames: fileA.1-3.png
tests/files/fileA.%04d.png [1-3]
```

This gives you stable, human-readable output for logs, manifests, UIs, and job
metadata.
