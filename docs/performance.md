# Performance

PySeq's performance matters most in sequence discovery and `lss` over large
file sets.

This project uses two complementary approaches:

- coarse regression tests in `tests/test_performance.py`
- one repeatable benchmark runner in `scripts/benchmark.py`

The regression tests should stay stable and fast enough for normal CI. The
benchmark runner is for collecting timing and profiling data over time, not
for enforcing fragile micro-optimizations in every pull request.

## Benchmark Runner

Current benchmark entry point:

- `scripts/benchmark.py`

Simple examples:

```bash
python scripts/benchmark.py
python scripts/benchmark.py --full
python scripts/benchmark.py --json /tmp/pyseq-main.json
python scripts/benchmark.py --compare /tmp/pyseq-main.json /tmp/pyseq-feature.json
```

What it measures:

- `get_sequences(...)` from an in-memory file list
- `get_sequences(...)` from a directory path
- `resolve_sequence(...)` against a padded on-disk sequence
- `lss` end-to-end subprocess runtime on the same synthetic dataset

Default synthetic dataset sizes:

- default: `100`, `1000`, `10000`
- `--full`: `100`, `1000`, `10000`, `50000`

You can override dataset sizes or iteration count:

```bash
python scripts/benchmark.py --sizes 100,1000,10000,50000 --iterations 7
```

## Local A/B Comparison

Use the same machine and same interpreter for both runs.

Example workflow:

```bash
# on baseline branch
python scripts/benchmark.py --full --json /tmp/pyseq-main.json

# switch branches
python scripts/benchmark.py --full --json /tmp/pyseq-feature.json

# compare
python scripts/benchmark.py --compare /tmp/pyseq-main.json /tmp/pyseq-feature.json
```

## Profiling

Profiling is enabled by default, but it runs in a separate pass after the
timed measurements. That means the timing samples stay clean while we still
capture where time is going.

Generated artifacts:

- one `.pstats` file per benchmark case
- one text summary per benchmark case, sorted by cumulative time

Default output location:

- `tmp/benchmarks/profiles/`

Useful options:

- `--no-profile` to skip profiling entirely
- `--profiles-dir <path>` to choose a different output directory

## Result Format

The benchmark runner can emit machine-readable JSON for local comparison, CI
artifacts, or published reports.

Example run payload:

```json
{
  "benchmarks": {
    "get_sequences_dir_1000": {
      "iterations": 5,
      "max_s": 0.043512,
      "mean_s": 0.041932,
      "median_s": 0.041704,
      "min_s": 0.040161,
      "samples_s": [0.040161, 0.041085, 0.041704, 0.043198, 0.043512]
    },
    "lss_1000": {
      "iterations": 5,
      "max_s": 0.139424,
      "mean_s": 0.133529,
      "median_s": 0.132611,
      "min_s": 0.129400,
      "samples_s": [0.129400, 0.131818, 0.132611, 0.134390, 0.139424]
    }
  },
  "branch": "feat/example",
  "commit": "abc1234",
  "iterations": 5,
  "kind": "benchmark",
  "platform": "Linux-6.x-x86_64",
  "profiled": true,
  "profiles_dir": "tmp/benchmarks/profiles/20260721T000000Z-feat-example-abc1234",
  "python": "3.11.x",
  "sizes": [100, 1000, 10000],
  "timestamp_utc": "2026-07-21T00:00:00+00:00"
}
```

Field notes:

- `kind` distinguishes normal benchmark runs from comparison payloads.
- `median_s` is the primary comparison value.
- `mean_s` is useful when the run-to-run spread is small.
- `samples_s` helps show spread directly.
- `branch` and `commit` make branch-to-branch comparisons easier to track.
- `profiles_dir` points to the profile output location for that run.
- `timestamp_utc`, `python`, and `platform` help when comparing results.

## Methodology

The benchmark runner:

- generates synthetic datasets in temporary directories
- uses `time.perf_counter()`
- warms up once before measuring
- collects several samples
- reports median, mean, min, and max
- profiles each case in a separate pass by default

This keeps the results useful without pretending that a shared CI runner is a
perfect benchmarking machine.

## Interpreting Results

Treat GitHub-hosted benchmark numbers as trend indicators, not as precise
absolute truth.

Good uses:

- spotting real regressions on the same machine
- comparing branch-to-branch trends on the same interpreter
- attaching timing evidence to performance-focused pull requests

Less reliable uses:

- failing builds on tiny percentage differences
- comparing results across different operating systems or Python versions
- drawing conclusions from a single run

If stronger consistency becomes important, prefer a self-hosted benchmark
runner with a stable machine configuration.
