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
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from pyseq import get_sequences  # noqa: E402
from pyseq.util import resolve_sequence  # noqa: E402


DEFAULT_SIZES = [100, 1000, 10000]
FULL_SIZES = [100, 1000, 10000, 50000]
DEFAULT_ITERATIONS = 5
FULL_ITERATIONS = 7
EXTRA_FILES_FACTOR = 0.1
PROFILE_TOP_FUNCTIONS = 25


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


def create_dataset(root, size, extra_files_factor=EXTRA_FILES_FACTOR):
    dataset = root / f"size_{size}"
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


def run_lss(path):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(LIB_ROOT)
        if not env.get("PYTHONPATH")
        else str(LIB_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    subprocess.run(
        [sys.executable, "-m", "pyseq.lss", str(path)],
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


def profile_lss_subprocess(path, stem, profiles_dir):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(LIB_ROOT)
        if not env.get("PYTHONPATH")
        else str(LIB_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    pstats_path = profiles_dir / f"{stem}.pstats"
    text_path = profiles_dir / f"{stem}.txt"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "cProfile",
            "-o",
            str(pstats_path),
            "-m",
            "pyseq.lss",
            str(path),
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


@contextmanager
def build_benchmarks(sizes):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cases = []

        for size in sizes:
            fixture = create_dataset(root, size)
            dataset_path = fixture["path"]
            file_names = fixture["file_names"]
            sequence_pattern = fixture["sequence_pattern"]

            cases.extend(
                [
                    {
                        "name": f"get_sequences_list_{size}",
                        "callable": lambda file_names=file_names: get_sequences(
                            file_names
                        ),
                        "profile_kind": "python",
                    },
                    {
                        "name": f"get_sequences_dir_{size}",
                        "callable": lambda dataset_path=dataset_path: get_sequences(
                            str(dataset_path)
                        ),
                        "profile_kind": "python",
                    },
                    {
                        "name": f"resolve_sequence_{size}",
                        "callable": lambda sequence_pattern=sequence_pattern: resolve_sequence(
                            sequence_pattern
                        ),
                        "profile_kind": "python",
                    },
                    {
                        "name": f"lss_{size}",
                        "callable": lambda dataset_path=dataset_path: run_lss(
                            dataset_path
                        ),
                        "profile_kind": "lss",
                        "path": dataset_path,
                    },
                ]
            )

        yield cases


def run_benchmarks(sizes, iterations, enable_profile, profiles_dir):
    with build_benchmarks(sizes) as cases:
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
                    profile_lss_subprocess(case["path"], case["name"], profiles_dir)

        return results


def build_run_payload(sizes, iterations, enable_profile, profiles_dir):
    branch = detect_git_branch()
    commit = detect_git_sha()
    actual_profiles_dir = profiles_dir
    if enable_profile and actual_profiles_dir is None:
        actual_profiles_dir = make_default_profiles_dir(branch, commit)

    benchmarks = run_benchmarks(
        sizes=sizes,
        iterations=iterations,
        enable_profile=enable_profile,
        profiles_dir=actual_profiles_dir,
    )

    return {
        "kind": "benchmark",
        "branch": branch,
        "commit": commit,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sizes": sizes,
        "iterations": iterations,
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
        },
        "candidate": {
            "branch": candidate.get("branch"),
            "commit": candidate.get("commit"),
        },
        "benchmarks": comparisons,
        "summary": {
            "median_delta_pct": median(deltas),
            "max_regression_pct": max(deltas),
            "max_improvement_pct": min(deltas),
        },
    }


def write_run_summary(payload, stream):
    print("# pyseq benchmarks", file=stream)
    print("", file=stream)
    print(
        f"Branch: `{payload['branch']}`  Commit: `{payload['commit']}`  Sizes: `{','.join(str(size) for size in payload['sizes'])}`  Iterations: `{payload['iterations']}`",
        file=stream,
    )
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
    args = parser.parse_args()

    if args.compare:
        payload = build_comparison(
            load_json(args.compare[0]),
            load_json(args.compare[1]),
        )
        if args.json_path:
            dump_json(payload, args.json_path)
        write_compare_summary(payload, sys.stdout)
        return

    sizes = args.sizes or (FULL_SIZES if args.full else DEFAULT_SIZES)
    iterations = args.iterations or (
        FULL_ITERATIONS if args.full else DEFAULT_ITERATIONS
    )
    profiles_dir = Path(args.profiles_dir) if args.profiles_dir else None
    payload = build_run_payload(
        sizes=sizes,
        iterations=iterations,
        enable_profile=not args.no_profile,
        profiles_dir=profiles_dir,
    )

    if args.json_path:
        dump_json(payload, args.json_path)
    write_run_summary(payload, sys.stdout)


if __name__ == "__main__":
    main()
