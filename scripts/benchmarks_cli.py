#!/usr/bin/env python3
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""CLI benchmarks for pyseq console tools."""

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


PROFILE_CONFIG = {
    "smoke": {"iterations": 3, "file_count": 200},
    "full": {"iterations": 5, "file_count": 1000},
}


CLI_MODULES = {
    "lss": "pyseq.lss",
    "stree": "pyseq.stree",
    "sfind": "pyseq.sfind",
    "sdiff": "pyseq.sdiff",
    "sstat": "pyseq.sstat",
}


def resolve_command(name):
    scripts_dir = sysconfig.get_path("scripts")
    candidates = [name]
    if os.name == "nt":
        candidates = [f"{name}.exe", f"{name}.cmd", f"{name}.bat", name]

    for candidate in candidates:
        path = os.path.join(scripts_dir, candidate)
        if os.path.exists(path):
            return [path]

    path = shutil.which(name)
    if path:
        return [path]

    return [sys.executable, "-m", CLI_MODULES[name]]


def measure(func, iterations, warmups=1):
    for _ in range(warmups):
        func()

    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        samples.append(time.perf_counter() - start)

    return {
        "median_s": statistics.median(samples),
        "min_s": min(samples),
        "max_s": max(samples),
        "iterations": iterations,
    }


def run_cli(command, *args):
    cmd = resolve_command(command) + list(args)
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def create_fixture_tree(root, file_count):
    nested = root / "nested" / "plates"
    nested.mkdir(parents=True, exist_ok=True)

    for frame in range(1, file_count + 1):
        (root / f"renderA.{frame:04d}.exr").write_text("frame\n")
        (root / f"renderB.{frame:04d}.exr").write_text("frame\n")

    for frame in range(1, max(10, file_count // 10) + 1):
        (nested / f"plate.{frame:04d}.png").write_text("frame\n")

    (root / "notes.txt").write_text("not a sequence\n")


def run_profile(profile):
    config = PROFILE_CONFIG[profile]
    results = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_tree(root, config["file_count"])

        seq_a = str(root / "renderA.%04d.exr")
        seq_b = str(root / "renderB.%04d.exr")

        results["lss_recursive"] = measure(
            lambda: run_cli("lss", "-r", str(root)),
            config["iterations"],
        )
        results["lss_format_x"] = measure(
            lambda: run_cli("lss", str(root), "-f", "%h%x%t"),
            config["iterations"],
        )
        results["stree"] = measure(
            lambda: run_cli("stree", str(root)),
            config["iterations"],
        )
        results["sfind_png"] = measure(
            lambda: run_cli("sfind", str(root), "-name", "*.png"),
            config["iterations"],
        )
        results["sdiff"] = measure(
            lambda: run_cli("sdiff", seq_a, seq_b),
            config["iterations"],
        )
        results["sstat"] = measure(
            lambda: run_cli("sstat", seq_a),
            config["iterations"],
        )

    return results


def build_payload(profile):
    return {
        "kind": "cli",
        "profile": profile,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "benchmarks": run_profile(profile),
    }


def write_summary(payload, stream):
    print(f"# pyseq CLI benchmarks ({payload['profile']})", file=stream)
    print("", file=stream)
    print("| Benchmark | Median (s) | Min (s) | Max (s) |", file=stream)
    print("| --- | ---: | ---: | ---: |", file=stream)
    for name, result in payload["benchmarks"].items():
        print(
            f"| `{name}` | {result['median_s']:.6f} | {result['min_s']:.6f} | {result['max_s']:.6f} |",
            file=stream,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILE_CONFIG), default="smoke")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.profile)

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")

    if args.summary:
        write_summary(payload, sys.stdout)

    if not args.json_path and not args.summary:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
