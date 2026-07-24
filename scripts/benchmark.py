#!/usr/bin/env python3
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Simple local benchmark runner for pyseq hotspots."""

import argparse
import cProfile
import io
import json
import os
import platform
import pstats
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
LIB_ROOT = REPO_ROOT / "lib"
SCRIPT_PATH = Path(__file__).resolve()
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

import pyseq  # noqa: E402
import pyseq.seq as pyseq_seq  # noqa: E402
from pyseq import get_sequences  # noqa: E402
from pyseq.util import resolve_sequence  # noqa: E402


DEFAULT_SIZES = [100, 1000, 10000]
FULL_SIZES = [100, 1000, 10000, 50000]
DEFAULT_ITERATIONS = 5
FULL_ITERATIONS = 7
EXTRA_FILES_FACTOR = 0.1
PROFILE_TOP_FUNCTIONS = 25
DEFAULT_SCENARIOS = ["contiguous", "mixed"]


def median(values):
    return statistics.median(values) if values else 0.0


def mean(values):
    return statistics.mean(values) if values else 0.0


def pct_delta(new_value, old_value):
    if old_value == 0:
        return 0.0
    return ((new_value / old_value) - 1.0) * 100.0


def parse_sizes(value):
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def parse_csv_list(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def detect_git_branch():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip() or "detached"
    except Exception:
        return "unknown"


def detect_git_sha():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def safe_path_token(value):
    return value.replace(os.sep, "-").replace("/", "-")


def make_default_profiles_dir(branch, commit):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        REPO_ROOT
        / "tmp"
        / "benchmarks"
        / "profiles"
        / f"{timestamp}-{safe_path_token(branch)}-{safe_path_token(commit)}"
    )


def benchmark_call(func, iterations, warmups=1):
    for _ in range(warmups):
        func()

    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        samples.append(time.perf_counter() - start)

    return {
        "iterations": iterations,
        "samples_s": samples,
        "median_s": median(samples),
        "mean_s": mean(samples),
        "min_s": min(samples),
        "max_s": max(samples),
    }


def create_contiguous_dataset(root, size, extra_files_factor=EXTRA_FILES_FACTOR):
    dataset = root / f"contiguous_{size}"
    dataset.mkdir(parents=True, exist_ok=True)

    for frame in range(1, size + 1):
        (dataset / f"renderA.{frame:08d}.exr").touch()

    extra_count = max(1, int(size * extra_files_factor))
    for index in range(extra_count):
        (dataset / f"note_{index:08d}.txt").touch()

    return {
        "path": dataset,
        "sequence_pattern": str(dataset / "renderA.%08d.exr"),
        "file_names": sorted(os.listdir(dataset)),
    }


def _partition_count(total, parts):
    if parts <= 0:
        return []
    base, remainder = divmod(total, parts)
    return [base + (1 if index < remainder else 0) for index in range(parts)]


def create_mixed_dataset(root, size, extra_files_factor=EXTRA_FILES_FACTOR):
    dataset = root / f"mixed_{size}"
    dataset.mkdir(parents=True, exist_ok=True)

    primary_count = max(1, int(size * 0.75))
    secondary_count = max(1, int(size * 0.08))
    tertiary_count = max(1, int(size * 0.04))
    quaternary_count = max(1, int(size * 0.04))

    gap_stride = max(50, size // 12 or 1)
    segment_lengths = _partition_count(primary_count, 9)
    frame = 1
    for segment_length in segment_lengths:
        for _ in range(segment_length):
            (dataset / f"base.{frame:08d}.png").touch()
            frame += 1
        frame += gap_stride

    secondary_start = 1001
    tertiary_start = 1001
    quaternary_start = 1001
    for offset in range(secondary_count):
        (
            dataset / f"big_buck_bunny_1080p_h264.{secondary_start + offset:08d}.png"
        ).touch()
    for offset in range(tertiary_count):
        (
            dataset
            / f"big_buck_bunny_1080p_h264_test.{tertiary_start + offset:08d}.png"
        ).touch()
    for offset in range(quaternary_count):
        (dataset / f"test.{quaternary_start + offset:08d}.png").touch()

    extra_count = max(1, int(size * extra_files_factor))
    for index in range(extra_count):
        (dataset / f"notes_{index:08d}.txt").touch()

    for tile in range(max(2, size // 2000 + 1)):
        for frame in range(101, 111):
            (dataset / f"bnc01_TinkSO_tx_{tile}_ty_{tile}.{frame:04d}.tif").touch()

    return {
        "path": dataset,
        "sequence_pattern": str(dataset / "base.%08d.png"),
        "file_names": sorted(os.listdir(dataset)),
    }


def create_existing_dataset(path, sequence_pattern=None, glob_pattern=None):
    dataset = Path(path).resolve()
    file_names = sorted(os.listdir(dataset))
    if glob_pattern:
        import fnmatch

        file_names = [
            name for name in file_names if fnmatch.fnmatch(name, glob_pattern)
        ]

    return {
        "path": dataset,
        "sequence_pattern": sequence_pattern,
        "file_names": file_names,
    }


def create_dataset(root, size, scenario):
    if scenario == "contiguous":
        return create_contiguous_dataset(root, size)
    if scenario == "mixed":
        return create_mixed_dataset(root, size)
    raise ValueError(f"Unknown benchmark scenario: {scenario}")


def run_lss(path, glob_pattern=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(LIB_ROOT)
        if not env.get("PYTHONPATH")
        else str(LIB_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    target = str(path)
    if glob_pattern:
        target = str(Path(path) / glob_pattern)
    subprocess.run(
        [sys.executable, "-m", "pyseq.lss", target],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def profile_python_callable(func, stem, profiles_dir):
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()

    pstats_path = profiles_dir / f"{stem}.pstats"
    text_path = profiles_dir / f"{stem}.txt"
    profiler.dump_stats(str(pstats_path))

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(PROFILE_TOP_FUNCTIONS)
    text_path.write_text(stream.getvalue(), encoding="utf-8")


def profile_lss_subprocess(path, stem, profiles_dir, glob_pattern=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(LIB_ROOT)
        if not env.get("PYTHONPATH")
        else str(LIB_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    pstats_path = profiles_dir / f"{stem}.pstats"
    text_path = profiles_dir / f"{stem}.txt"
    target = str(path)
    if glob_pattern:
        target = str(Path(path) / glob_pattern)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "cProfile",
            "-o",
            str(pstats_path),
            "-m",
            "pyseq.lss",
            target,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stream = io.StringIO()
    stats = pstats.Stats(str(pstats_path), stream=stream).sort_stats("cumulative")
    stats.print_stats(PROFILE_TOP_FUNCTIONS)
    text_path.write_text(stream.getvalue(), encoding="utf-8")


def _path_stem(path):
    return safe_path_token(str(Path(path).resolve()))


@contextmanager
def build_benchmarks(
    sizes=None,
    scenarios=None,
    path=None,
    sequence_pattern=None,
    glob_pattern=None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        cases = []
        fixtures = []

        if path:
            fixtures.append(
                {
                    "label": _path_stem(path),
                    **create_existing_dataset(
                        path,
                        sequence_pattern=sequence_pattern,
                        glob_pattern=glob_pattern,
                    ),
                }
            )
        else:
            root = Path(tmpdir)
            selected_scenarios = scenarios or DEFAULT_SCENARIOS
            for size in sizes:
                for scenario in selected_scenarios:
                    fixture = create_dataset(root, size, scenario)
                    fixtures.append({"label": f"{scenario}_{size}", **fixture})

        for fixture in fixtures:
            dataset_path = fixture["path"]
            file_names = fixture["file_names"]
            sequence_pattern = fixture["sequence_pattern"]
            label = fixture["label"]

            cases.extend(
                [
                    {
                        "name": f"get_sequences_list_{label}",
                        "callable": lambda file_names=file_names: get_sequences(
                            file_names
                        ),
                        "profile_kind": "python",
                    },
                    {
                        "name": f"get_sequences_dir_{label}",
                        "callable": lambda dataset_path=dataset_path, glob_pattern=glob_pattern: get_sequences(
                            str(Path(dataset_path) / glob_pattern)
                            if glob_pattern
                            else str(dataset_path)
                        ),
                        "profile_kind": "python",
                    },
                    {
                        "name": f"lss_{label}",
                        "callable": lambda dataset_path=dataset_path, glob_pattern=glob_pattern: run_lss(
                            dataset_path, glob_pattern=glob_pattern
                        ),
                        "profile_kind": "lss",
                        "path": dataset_path,
                        "glob_pattern": glob_pattern,
                    },
                ]
            )
            if sequence_pattern:
                cases.append(
                    {
                        "name": f"resolve_sequence_{label}",
                        "callable": lambda sequence_pattern=sequence_pattern: resolve_sequence(
                            sequence_pattern
                        ),
                        "profile_kind": "python",
                    }
                )

        yield cases


def run_benchmarks(
    sizes,
    scenarios,
    iterations,
    enable_profile,
    profiles_dir,
    path=None,
    sequence_pattern=None,
    glob_pattern=None,
):
    with build_benchmarks(
        sizes=sizes,
        scenarios=scenarios,
        path=path,
        sequence_pattern=sequence_pattern,
        glob_pattern=glob_pattern,
    ) as cases:
        results = {}
        for case in cases:
            results[case["name"]] = benchmark_call(case["callable"], iterations)

        if enable_profile:
            profiles_dir.mkdir(parents=True, exist_ok=True)
            for case in cases:
                if case["profile_kind"] == "python":
                    profile_python_callable(
                        case["callable"], case["name"], profiles_dir
                    )
                else:
                    profile_lss_subprocess(
                        case["path"],
                        case["name"],
                        profiles_dir,
                        glob_pattern=case.get("glob_pattern"),
                    )

        return results


def build_run_payload(
    sizes,
    scenarios,
    iterations,
    enable_profile,
    profiles_dir,
    path=None,
    sequence_pattern=None,
    glob_pattern=None,
):
    branch = detect_git_branch()
    commit = detect_git_sha()
    actual_profiles_dir = profiles_dir
    if enable_profile and actual_profiles_dir is None:
        actual_profiles_dir = make_default_profiles_dir(branch, commit)

    benchmarks = run_benchmarks(
        sizes=sizes,
        scenarios=scenarios,
        iterations=iterations,
        enable_profile=enable_profile,
        profiles_dir=actual_profiles_dir,
        path=path,
        sequence_pattern=sequence_pattern,
        glob_pattern=glob_pattern,
    )

    return {
        "kind": "benchmark",
        "branch": branch,
        "commit": commit,
        "repo_root": str(REPO_ROOT),
        "lib_root": str(LIB_ROOT),
        "script_path": str(SCRIPT_PATH),
        "python_executable": sys.executable,
        "pyseq_file": getattr(pyseq, "__file__", None),
        "pyseq_seq_file": getattr(pyseq_seq, "__file__", None),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sizes": sizes,
        "scenarios": scenarios,
        "iterations": iterations,
        "path": str(Path(path).resolve()) if path else None,
        "sequence_pattern": sequence_pattern,
        "glob_pattern": glob_pattern,
        "profiled": enable_profile,
        "profiles_dir": str(actual_profiles_dir) if actual_profiles_dir else None,
        "benchmarks": benchmarks,
    }


def build_comparison(baseline, candidate):
    names = sorted(set(baseline["benchmarks"]) & set(candidate["benchmarks"]))
    comparisons = []
    for name in names:
        before = baseline["benchmarks"][name]
        after = candidate["benchmarks"][name]
        comparisons.append(
            {
                "benchmark": name,
                "baseline_median_s": before["median_s"],
                "candidate_median_s": after["median_s"],
                "delta_s": after["median_s"] - before["median_s"],
                "delta_pct": pct_delta(after["median_s"], before["median_s"]),
            }
        )

    deltas = [row["delta_pct"] for row in comparisons]
    return {
        "kind": "benchmark-compare",
        "baseline": {
            "branch": baseline.get("branch"),
            "commit": baseline.get("commit"),
            "repo_root": baseline.get("repo_root"),
            "lib_root": baseline.get("lib_root"),
            "script_path": baseline.get("script_path"),
            "python_executable": baseline.get("python_executable"),
            "pyseq_file": baseline.get("pyseq_file"),
            "pyseq_seq_file": baseline.get("pyseq_seq_file"),
        },
        "candidate": {
            "branch": candidate.get("branch"),
            "commit": candidate.get("commit"),
            "repo_root": candidate.get("repo_root"),
            "lib_root": candidate.get("lib_root"),
            "script_path": candidate.get("script_path"),
            "python_executable": candidate.get("python_executable"),
            "pyseq_file": candidate.get("pyseq_file"),
            "pyseq_seq_file": candidate.get("pyseq_seq_file"),
        },
        "benchmarks": comparisons,
        "summary": {
            "median_delta_pct": median(deltas),
            "max_regression_pct": max(deltas) if deltas else 0.0,
            "max_improvement_pct": min(deltas) if deltas else 0.0,
            "benchmark_count": len(comparisons),
        },
    }


def enforce_regression_threshold(payload, threshold_pct):
    regressions = [
        row for row in payload["benchmarks"] if row["delta_pct"] > threshold_pct
    ]
    if regressions:
        worst = max(regressions, key=lambda row: row["delta_pct"])
        raise SystemExit(
            "Regression threshold exceeded: "
            f"{len(regressions)} benchmark(s) slower than +{threshold_pct:.2f}% "
            f"(worst: {worst['benchmark']} at {worst['delta_pct']:+.2f}%)"
        )


def write_run_summary(payload, stream):
    print("# pyseq benchmarks", file=stream)
    print("", file=stream)
    print(
        f"Branch: `{payload['branch']}`  Commit: `{payload['commit']}`  Sizes: `{','.join(str(size) for size in payload['sizes']) if payload['sizes'] else 'custom'}`  Iterations: `{payload['iterations']}`",
        file=stream,
    )
    print(f"Repo: `{payload['repo_root']}`", file=stream)
    print(f"Lib: `{payload['lib_root']}`", file=stream)
    print(f"Python: `{payload['python_executable']}`", file=stream)
    if payload.get("scenarios"):
        print(
            f"Scenarios: `{','.join(payload['scenarios'])}`",
            file=stream,
        )
    if payload.get("pyseq_file"):
        print(f"PySeq: `{payload['pyseq_file']}`", file=stream)
    if payload.get("pyseq_seq_file"):
        print(f"PySeq seq: `{payload['pyseq_seq_file']}`", file=stream)
    if payload.get("path"):
        print(f"Path: `{payload['path']}`", file=stream)
    if payload.get("glob_pattern"):
        print(f"Glob: `{payload['glob_pattern']}`", file=stream)
    if payload.get("sequence_pattern"):
        print(f"Sequence pattern: `{payload['sequence_pattern']}`", file=stream)
    if payload["profiled"] and payload["profiles_dir"]:
        print(f"Profiles: `{payload['profiles_dir']}`", file=stream)
    print("", file=stream)
    print("| Benchmark | Median (s) | Mean (s) | Min (s) | Max (s) |", file=stream)
    print("| --- | ---: | ---: | ---: | ---: |", file=stream)
    for name, result in payload["benchmarks"].items():
        print(
            f"| `{name}` | {result['median_s']:.6f} | {result['mean_s']:.6f} | {result['min_s']:.6f} | {result['max_s']:.6f} |",
            file=stream,
        )


def write_compare_summary(payload, stream):
    print("# pyseq benchmark comparison", file=stream)
    print("", file=stream)
    print(
        f"Baseline: `{payload['baseline']['branch']}` `{payload['baseline']['commit']}`  Candidate: `{payload['candidate']['branch']}` `{payload['candidate']['commit']}`",
        file=stream,
    )
    if payload["baseline"].get("lib_root") or payload["candidate"].get("lib_root"):
        print(
            f"Baseline lib: `{payload['baseline'].get('lib_root')}`  Candidate lib: `{payload['candidate'].get('lib_root')}`",
            file=stream,
        )
    if payload["baseline"].get("python_executable") or payload["candidate"].get(
        "python_executable"
    ):
        print(
            f"Baseline python: `{payload['baseline'].get('python_executable')}`  Candidate python: `{payload['candidate'].get('python_executable')}`",
            file=stream,
        )
    if payload["baseline"].get("pyseq_file") or payload["candidate"].get("pyseq_file"):
        print(
            f"Baseline pyseq: `{payload['baseline'].get('pyseq_file')}`  Candidate pyseq: `{payload['candidate'].get('pyseq_file')}`",
            file=stream,
        )
    if payload["baseline"].get("pyseq_seq_file") or payload["candidate"].get(
        "pyseq_seq_file"
    ):
        print(
            f"Baseline pyseq.seq: `{payload['baseline'].get('pyseq_seq_file')}`  Candidate pyseq.seq: `{payload['candidate'].get('pyseq_seq_file')}`",
            file=stream,
        )
    print(
        "Summary: "
        f"`{payload['summary']['benchmark_count']}` benchmarks  "
        f"median delta `{payload['summary']['median_delta_pct']:+.2f}%`  "
        f"max regression `{payload['summary']['max_regression_pct']:+.2f}%`",
        file=stream,
    )
    print("", file=stream)
    print(
        "| Benchmark | Baseline Median (s) | Candidate Median (s) | Delta (s) | Delta (%) |",
        file=stream,
    )
    print("| --- | ---: | ---: | ---: | ---: |", file=stream)
    for row in payload["benchmarks"]:
        print(
            f"| `{row['benchmark']}` | {row['baseline_median_s']:.6f} | {row['candidate_median_s']:.6f} | {row['delta_s']:.6f} | {row['delta_pct']:+.2f}% |",
            file=stream,
        )


def dump_json(payload, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE_JSON", "CANDIDATE_JSON"),
        help="Compare two benchmark JSON files instead of running benchmarks",
    )
    parser.add_argument("--full", action="store_true", help="Run larger default sizes")
    parser.add_argument(
        "--sizes",
        type=parse_sizes,
        help="Comma-separated dataset sizes, for example: 100,1000,10000,50000",
    )
    parser.add_argument(
        "--scenarios",
        type=parse_csv_list,
        help="Comma-separated synthetic scenarios, for example: contiguous,mixed",
    )
    parser.add_argument(
        "--iterations", type=int, help="Override timing iteration count"
    )
    parser.add_argument("--json", dest="json_path", help="Write JSON output to a file")
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Skip the separate profiling pass",
    )
    parser.add_argument(
        "--profiles-dir",
        help="Directory for generated .pstats and text profile summaries",
    )
    parser.add_argument(
        "--path",
        help="Benchmark an existing directory instead of synthetic datasets",
    )
    parser.add_argument(
        "--glob",
        dest="glob_pattern",
        help="Optional glob pattern for lss and file list filtering when using --path",
    )
    parser.add_argument(
        "--sequence-pattern",
        help="Optional compressed sequence pattern for resolve_sequence when using --path",
    )
    parser.add_argument(
        "--fail-on-regression-pct",
        type=float,
        help="Exit non-zero when any compared benchmark regresses by more than this percentage",
    )
    args = parser.parse_args()

    if args.compare:
        payload = build_comparison(
            load_json(args.compare[0]),
            load_json(args.compare[1]),
        )
        if args.json_path:
            dump_json(payload, args.json_path)
        write_compare_summary(payload, sys.stdout)
        if args.fail_on_regression_pct is not None:
            enforce_regression_threshold(payload, args.fail_on_regression_pct)
        return

    sizes = (
        None
        if args.path
        else (args.sizes or (FULL_SIZES if args.full else DEFAULT_SIZES))
    )
    scenarios = None if args.path else (args.scenarios or DEFAULT_SCENARIOS)
    iterations = args.iterations or (
        FULL_ITERATIONS if args.full else DEFAULT_ITERATIONS
    )
    profiles_dir = Path(args.profiles_dir) if args.profiles_dir else None
    payload = build_run_payload(
        sizes=sizes,
        scenarios=scenarios,
        iterations=iterations,
        enable_profile=not args.no_profile,
        profiles_dir=profiles_dir,
        path=args.path,
        sequence_pattern=args.sequence_pattern,
        glob_pattern=args.glob_pattern,
    )

    if args.json_path:
        dump_json(payload, args.json_path)
    write_run_summary(payload, sys.stdout)


if __name__ == "__main__":
    main()
