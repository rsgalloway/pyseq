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
python scripts/benchmark.py --scenarios contiguous,mixed
python scripts/benchmark.py --path /project/shot/frames --iterations 5
python scripts/benchmark.py --path /project/shot/frames --glob "*.exr" --iterations 5
python scripts/benchmark.py --compare /tmp/pyseq-main.json /tmp/pyseq-feature.json
```

What it measures:

- `get_sequences(...)` from an in-memory file list
- `get_sequences(...)` from a directory path
- `resolve_sequence(...)` against a padded on-disk sequence
- `lss` end-to-end subprocess runtime on the same synthetic dataset

Synthetic scenarios:

- `contiguous`: one large primary sequence with light non-sequence noise
- `mixed`: a more realistic directory with a dominant gapped sequence,
  several neighboring sequences, and unrelated files

When using `--path`, the runner benchmarks an existing directory instead of a
synthetic dataset. This is useful for validating results against real-world
sequence layouts that may not be modeled well by generated fixtures.

Default synthetic dataset sizes:

- default: `100`, `1000`, `10000`
- `--full`: `100`, `1000`, `10000`, `50000`

Default synthetic scenarios:

- `contiguous`
- `mixed`

You can override dataset sizes or iteration count:

```bash
python scripts/benchmark.py --sizes 100,1000,10000,50000 --iterations 7
python scripts/benchmark.py --sizes 1000,10000 --scenarios mixed --iterations 7
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

For real-world validation, use the same workflow against an existing directory:

```bash
# on baseline branch
python scripts/benchmark.py --path /project/shot/frames --iterations 5 --json /tmp/pyseq-main.json

# switch branches
python scripts/benchmark.py --path /project/shot/frames --iterations 5 --json /tmp/pyseq-feature.json

# compare
python scripts/benchmark.py --compare /tmp/pyseq-main.json /tmp/pyseq-feature.json
```

## Benchmark Hygiene

Before trusting an A/B result, make sure both runs use:

- the same terminal/session state
- the same Python interpreter or virtualenv
- the same benchmark script revision
- the same target directory or synthetic dataset shape

The benchmark summary and JSON now record:

- `python_executable`
- `lib_root`
- `pyseq_file`
- `pyseq_seq_file`

Check those fields before drawing conclusions from a comparison. If they do
not match your expectations, fix the environment first and rerun.

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
- `--scenarios <list>` to choose synthetic directory shapes
- `--fail-on-regression-pct <value>` to turn a compare run into a CI gate

## CI Automation

The GitHub Actions benchmark workflow runs pull request comparisons in one job
on one GitHub-hosted runner.

For pull requests it:

- checks out the candidate branch
- checks out the pull request base commit in a sibling worktree
- runs the same benchmark script revision against both trees
- compares the two JSON result sets
- uploads both result sets and profile artifacts
- posts a sticky pull request comment with the comparison summary
- fails the workflow if any benchmark regresses by more than `5%`

The pull request suite uses synthetic datasets only, so it is best treated as
a regression guardrail. For more realistic validation, keep using local
`--path` runs against representative production-style directories.

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
  "lib_root": "/path/to/pyseq/lib",
  "platform": "Linux-6.x-x86_64",
  "profiled": true,
  "pyseq_file": "/path/to/pyseq/lib/pyseq/__init__.py",
  "pyseq_seq_file": "/path/to/pyseq/lib/pyseq/seq.py",
  "python_executable": "/path/to/venv/bin/python",
  "profiles_dir": "tmp/benchmarks/profiles/20260721T000000Z-feat-example-abc1234",
  "python": "3.11.x",
  "repo_root": "/path/to/pyseq",
  "scenarios": ["contiguous", "mixed"],
  "script_path": "/path/to/pyseq/scripts/benchmark.py",
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
- `repo_root`, `lib_root`, `script_path`, and `python_executable` show
  exactly which source tree and interpreter were used.
- `scenarios` records which synthetic directory shapes were exercised.
- `pyseq_file` and `pyseq_seq_file` confirm which imported package files were
  actually exercised.
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
