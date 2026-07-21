# Performance

PySeq's performance matters most in sequence discovery, range formatting, and
CLI workflows over large file sets.

This project uses two complementary approaches:

- coarse regression tests in `tests/test_performance.py`
- repeatable benchmark scripts under `scripts/`

The regression tests should stay stable and fast enough for normal CI. The
benchmark scripts are for collecting timing data over time, not for enforcing
fragile micro-optimizations in every pull request.

## Benchmark Scripts

Current benchmark entry points:

- `scripts/benchmarks_core.py`
- `scripts/benchmarks_cli.py`

Both scripts support:

- `--profile smoke`
- `--profile full`
- `--json <path>`
- `--summary`

Examples:

```bash
python scripts/benchmarks_core.py --profile smoke --summary
python scripts/benchmarks_core.py --profile full --json core-benchmarks.json
python scripts/benchmarks_cli.py --profile smoke --summary
```

## Result Format

Both benchmark scripts can emit machine-readable JSON for CI artifacts,
historical snapshots, or local comparison.

Example core benchmark payload:

```json
{
  "benchmarks": {
    "sequence_construct_1000": {
      "iterations": 5,
      "max_s": 0.043952,
      "median_s": 0.041054,
      "min_s": 0.037981
    },
    "uncompress_stepped_10k": {
      "iterations": 5,
      "max_s": 0.153435,
      "median_s": 0.132808,
      "min_s": 0.130189
    }
  },
  "kind": "core",
  "platform": "Linux-6.x-x86_64",
  "profile": "smoke",
  "python": "3.11.x",
  "timestamp_utc": "2026-07-21T00:00:00+00:00"
}
```

Example CLI benchmark payload:

```json
{
  "benchmarks": {
    "lss_recursive": {
      "iterations": 3,
      "max_s": 0.110399,
      "median_s": 0.103545,
      "min_s": 0.101037
    },
    "sfind_png": {
      "iterations": 3,
      "max_s": 0.095798,
      "median_s": 0.093574,
      "min_s": 0.093541
    }
  },
  "kind": "cli",
  "platform": "Linux-6.x-x86_64",
  "profile": "smoke",
  "python": "3.11.x",
  "timestamp_utc": "2026-07-21T00:00:00+00:00"
}
```

Field notes:

- `kind` distinguishes library benchmarks from CLI benchmarks.
- `profile` indicates whether the run used the `smoke` or `full` dataset.
- `median_s` is the primary comparison value.
- `min_s` and `max_s` help show runner noise and spread.
- `timestamp_utc`, `python`, and `platform` are useful when comparing
  artifacts across runs.

## What We Measure

### Core library benchmarks

- `Sequence(...)` construction at fixed scales
- `get_sequences(...)` on mixed file lists
- `uncompress(...)` for contiguous and stepped ranges
- `%M` formatting on sparse huge ranges
- stepped range parsing and formatting
- `resolve_sequence_reference(...)` for stepped serialized references

### CLI benchmarks

- `lss`
- `stree`
- `sfind`
- `sdiff`
- `sstat`

CLI benchmarks intentionally include subprocess overhead because that is part
of the real user-facing cost.

## Profiles

### `smoke`

Use this in normal CI and pull-request workflows.

Goals:

- catch catastrophic regressions
- keep runtime short
- publish comparable results

### `full`

Use this for scheduled runs or manual benchmarking.

Goals:

- collect more stable medians
- exercise larger synthetic datasets
- provide release-readiness data

## Methodology

The benchmark scripts:

- generate synthetic datasets in memory or temporary directories
- use `time.perf_counter()`
- warm up once before measuring
- collect several samples
- report median, min, and max

This keeps the results useful without pretending that a shared CI runner is a
perfect benchmarking machine.

## Interpreting Results

Treat GitHub-hosted benchmark numbers as trend indicators, not as precise
absolute truth.

Good uses:

- spotting order-of-magnitude regressions
- comparing broad trends on the same workflow
- attaching timing evidence to performance-focused pull requests

Less reliable uses:

- failing builds on small percentage differences
- comparing results across different operating systems or Python versions
- drawing conclusions from a single run

If stronger consistency becomes important, prefer a self-hosted benchmark
runner with a stable machine configuration.
