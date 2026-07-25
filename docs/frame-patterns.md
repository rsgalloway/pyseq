# Frame Patterns

Use `${PYSEQ_FRAME_PATTERN}` to define custom regular expressions for
identifying frame numbers.

Signed frame numbers such as `render.-0010.exr` are opt-in. Enable them with:

```bash
export PYSEQ_ALLOW_NEGATIVE_FRAMES=1
```

## Example

If frames are always preceded by an underscore:

```bash
export PYSEQ_FRAME_PATTERN="_\\d+"
```

Environment variables can be defined anywhere in your shell environment, or if
you use `envstack`, add them to `pyseq.env` and make sure that file is found in
`${ENVPATH}`:

```bash
export ENVPATH=/path/to/env/files
```

## Pattern Examples

Examples of regex patterns can be found in `pyseq.env`:

```yaml
# matches all numbers, the most flexible
PYSEQ_FRAME_PATTERN: \d+

# excludes version numbers, e.g. file_v001.1001.exr
PYSEQ_FRAME_PATTERN: ([^v\d])\d+

# frame numbers are dot-delimited, e.g. file.v1.1001.exr
PYSEQ_FRAME_PATTERN: \.\d+\.

# frame numbers start with an underscore, e.g. file_v1_1001.exr
PYSEQ_FRAME_PATTERN: _\d+

# allow signed frame numbers in explicit ranges and filename discovery
PYSEQ_ALLOW_NEGATIVE_FRAMES: ${PYSEQ_ALLOW_NEGATIVE_FRAMES:=0}
```
