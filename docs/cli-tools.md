# CLI Tools Reference

PySeq includes a set of sequence-aware command-line tools for browsing and
manipulating frame-based media.

## `lss`

List files and group matching names into sequences.

```bash
lss tests/files
lss -r tests
lss tests/files/*.png -f "%l %h%r%t %M"
lss tests/files/*.png -f "%h%p%t %x"
```

## `stree`

Display a tree view while collapsing numbered files into sequence entries.

```bash
stree tests/
```

## `sfind`

Recursively search for files and return grouped sequence results.

```bash
sfind ./tests -name "*.png"
```

## `sdiff`

Compare two sequences or frame ranges.

```bash
sdiff comp_A.%04d.exr comp_B.%04d.exr
```

## `sstat`

Print detailed information for a sequence, including frame range formatting.

```bash
sstat render.%04d.exr
sstat --json render.%04d.exr
```

## `scopy`

Copy a sequence into another directory or renumber it into a new destination
sequence.

```bash
scopy input.%04d.exr output/
scopy input.1-100.exr scene.1001-1100.exr
scopy input.%04d.exr\ 1001-1010x2 output/
```

## `smv`

Move or rename a sequence, with optional renumbering.

```bash
smv old.%04d.exr new.%04d.exr
smv old.%04d.exr archive/ --renumber 1001
smv old.%04d.exr\ 1001-1005x2 new.%04d.exr\ 2001-2003
```

## `srm`

Remove a sequence or a frame range embedded in a compressed sequence string.

```bash
srm input.1-100.exr
srm input.%04d.exr\ 1001-1010x2
```

## Common Pipeline Use Cases

- Summarize render outputs in a directory.
- Detect missing frames before publish or delivery.
- Rename or move sequences while preserving frame numbering intent.
- Build reports over image, cache, or simulation output directories.
