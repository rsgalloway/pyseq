# Contributing

PySeq changes should stay small, clear, and performance-aware.

## Development Basics

- Run the unit tests for code changes:
  `pytest tests -q`
- Prefer focused changes over broad refactors unless the refactor is the task.
- Keep the default filename discovery path permissive and fast.

## Performance

Performance is a project priority, especially for:

- `lss`
- `get_sequences(...)`
- `resolve_sequence(...)`

When changing code under `lib/pyseq/`, contributors should treat performance
as part of correctness.

Current benchmark policy:

- pull requests run synthetic benchmark comparisons against the base branch
- benchmark deltas stay visible in the pull request comment
- the benchmark workflow fails when a regression exceeds both `3%` and `0.005s`
- repeated small regressions in the same hotspot should be investigated before
  they accumulate across releases

Recommended workflow for performance-sensitive changes:

1. Run the unit tests.
2. Run `python scripts/benchmark.py --json /tmp/pyseq-feature.json`.
3. Compare against a baseline branch or commit with
   `python scripts/benchmark.py --compare /tmp/pyseq-main.json /tmp/pyseq-feature.json`.
4. If a hotspot regresses, collect profiles and inspect them before merging.

For more detail, see [docs/performance.md](docs/performance.md).
