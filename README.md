PySeq
=====

PySeq is a python module that finds groups of items that follow a naming
convention containing  a numerical sequence index (e.g. fileA.001.png,
fileA.002.png, fileA.003.png...) and serializes them into a compressed sequence
string representing the entire sequence (e.g. fileA.1-3.png). It should work
regardless of where the numerical sequence index is embedded in the name. For
examples, see basic usage below or http://rsgalloway.github.io/pyseq

## Installation

The easiest way to install pyseq:

```bash
$ pip install -U pyseq
```

#### distman

If installing from source you can use [distman](https://github.com/rsgalloway/distman)
to install pyseq using the provided `dist.json` file:

```bash
$ distman [-d]
```

Using distman will deploy the targets defined in the `dist.json` file to the
root folder defined by `$DEPLOY_ROOT`.

#### envstack

PySeq uses [envstack](https://github.com/rsgalloway/envstack) to manage configs
via environment variables.

```bash
$ envstack pyseq
PYSEQ_RANGE_SEP=, 
PYSEQ_STRICT_PAD=0
STACK=pyseq
```

## Basic Usage

Using the "z1" file sequence example in the "tests" directory, we start by
listing the directory
contents using `ls`:

```bash
$ ls tests/files/z1*
tests/files/z1_001_v1.1.png  tests/files/z1_001_v1.4.png  tests/files/z1_002_v1.3.png   tests/files/z1_002_v2.11.png
tests/files/z1_001_v1.2.png  tests/files/z1_002_v1.1.png  tests/files/z1_002_v1.4.png   tests/files/z1_002_v2.12.png
tests/files/z1_001_v1.3.png  tests/files/z1_002_v1.2.png  tests/files/z1_002_v2.10.png  tests/files/z1_002_v2.9.png
```

Now we list the same directory contents using `lss`, which will find the
sequences and display them in the default compressed format:

```bash
$ lss tests/files/z1*
   4 z1_001_v1.%d.png [1-4]
   4 z1_002_v1.%d.png [1-4]
   4 z1_002_v2.%d.png [9-12]
```

With a custom format:

```bash
$ lss tests/files/z1* -f "%h%r%t"
z1_001_v1.1-4.png
z1_002_v1.1-4.png
z1_002_v2.9-12.png
```

Recursive:

```bash
$ lss -r tests
tests
├── test_pyseq.py
└── files
    ├── 012_vb_110_v001.1-10.png
    ├── 012_vb_110_v002.1-10.png
    ├── a.1-14.tga
    ├── alpha.txt
    ├── bnc01_TinkSO_tx_0_ty_0.101-105.tif
    ├── bnc01_TinkSO_tx_0_ty_1.101-105.tif
    ├── bnc01_TinkSO_tx_1_ty_0.101-105.tif
    ├── bnc01_TinkSO_tx_1_ty_1.101-105.tif
    ├── file.1-2.tif
    ├── file.info.03.rgb
    ├── file01.1-4.j2k
    ├── file01_40-43.rgb
    ├── file02_44-47.rgb
    ├── file1-4.03.rgb
    ├── fileA.1-3.jpg
    ├── fileA.1-3.png
    ├── file_02.tif
    ├── z1_001_v1.1-4.png
    ├── z1_002_v1.1-4.png
    └── z1_002_v2.9-12.png
```

## API Examples

Compression, or serialization, of lists of items:

```python
>>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
>>> print(s)
file.1-3.jpg
>>> s.append('file.0006.jpg')
>>> print(s.format("%h%p%t %R"))
file.%04d.jpg [1-3, 6]
```

Uncompression, or deserialization, of compressed sequences strings:

```python
>>> s = uncompress('./tests/012_vb_110_v001.%04d.png 1-1001', fmt='%h%p%t %r')
>>> len(s)
1001
>>> print(s.format('%04l %h%p%t %R'))
1001 012_vb_110_v001.%04d.png [1-1001]
```

## Formatting

The following directives can be embedded in the format string.

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
| `%d`      | disk usage                           |
| `%H`      | disk usage (human readable)          |
| `%D`      | parent directory                     |
| `%h`      | string preceding sequence number     |
| `%t`      | string after the sequence number     |

Here are some examples using `lss -f <format>` and `seq.format(..)`:

Using `lss -f <format>`:

```bash
$ $ lss tests/files/a*.tga -f "%h%r%t"
a.1-14.tga
$ lss tests/files/a*.tga -f "%l %h%r%t"
7 a.1-14.tga
$ lss tests/files/a*.tga -f "%l %h%r%t %M"
7 a.1-14.tga [4-9, 11]
```

In Python, using `seq.format(..)`:

```python
>>> s = pyseq.get_sequences("tests/files/a*.tga")[0]
>>> print(s.format("%h%r%t"))
a.1-14.tga
>>> print(s.format("%l %h%r%t"))
7 a.1-14.tga
>>> print(s.format("%l %h%r%t %M"))
7 a.1-14.tga [4-9, 11]
```

## Testing

To run the unit tests, simply run `pytest` in a shell:

```bash
$ pytest test/ -s
```

Or if you don't have `pytest`, you can run:

```bash
$ python tests/test_pyseq.py
```