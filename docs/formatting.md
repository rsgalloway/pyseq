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
| `%d`      | disk usage                           |
| `%H`      | disk usage (human readable)          |
| `%D`      | parent directory                     |
| `%h`      | string preceding sequence number     |
| `%t`      | string after the sequence number     |

## CLI Examples

```bash
$ lss tests/files/a*.tga -f "%h%r%t"
a.1-14.tga

$ lss tests/files/a*.tga -f "%l %h%r%t"
7 a.1-14.tga

$ lss tests/files/a*.tga -f "%l %h%r%t %M"
7 a.1-14.tga [4-9, 11]
```

## Python Examples

```python
import pyseq

seq = pyseq.get_sequences("tests/files/a*.tga")[0]

print(seq.format("%h%r%t"))
print(seq.format("%l %h%r%t"))
print(seq.format("%l %h%r%t %M"))
```

Expected output:

```text
a.1-14.tga
7 a.1-14.tga
7 a.1-14.tga [4-9, 11]
```
