# Formatting Reference

PySeq sequences can be rendered with format directives in both Python and the
CLI tools.

## Directives

| Directive | Meaning                              |
|-----------|--------------------------------------|
| `%s`      | sequence start                       |
| `%e`      | sequence end                         |
| `%l`      | sequence length                      |
| `%f`      | list of found files                  |
| `%m`      | list of missing files                |
| `%M`      | explicit missing files [11-14,19-21] |
| `%p`      | padding, e.g. %06d                   |
| `%r`      | implied range, start-end             |
| `%R`      | explicit broken range, [1-10, 15-20] |
| `%x`      | stepped explicit range, 1-10x2,20    |
| `%d`      | disk usage                           |
| `%H`      | disk usage (human readable)          |
| `%D`      | parent directory                     |
| `%h`      | string preceding sequence number     |
| `%t`      | string after the sequence number     |

## Serialized Range Syntax

PySeq supports the following serialized range forms when parsing sequence
strings with `uncompress()` and the sequence-aware CLI tools:

```text
1001
1001-1100
1001-1100x2
1001-1100x10, 1200, 1300-1320x5
10-1x3
-10--1x3
```

Notes:

- `xN` means "every Nth frame" anchored to the segment start.
- Descending ranges are accepted when parsing, but `Sequence.frames()` and
  `%x` formatting normalize frames into ascending order.
- `%x` uses compact canonical formatting with no spaces after commas.
- Signed frame numbers are supported in serialized range strings and in
  on-disk filename patterns such as `render.-0010.exr`.

## CLI Examples

```bash
$ lss tests/files/a*.tga -f "%h%r%t"
a.1-14.tga

$ lss tests/files/a*.tga -f "%l %h%r%t"
7 a.1-14.tga

$ lss tests/files/a*.tga -f "%l %h%r%t %M"
7 a.1-14.tga [4-9, 11]

$ python3 -c "import pyseq; s = pyseq.uncompress('render.%04d.exr 1001-1010x3', fmt='%h%p%t %x'); print(s.format('%x'))"
1001-1010x3
```

## Python Examples

```python
import pyseq

seq = pyseq.get_sequences("tests/files/a*.tga")[0]

print(seq.format("%h%r%t"))
print(seq.format("%l %h%r%t"))
print(seq.format("%l %h%r%t %M"))
print(pyseq.uncompress("render.%04d.exr 1001-1010x3", fmt="%h%p%t %x").format("%x"))
```

Expected output:

```text
a.1-14.tga
7 a.1-14.tga
7 a.1-14.tga [4-9, 11]
1001-1010x3
```
