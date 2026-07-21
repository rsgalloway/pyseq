#!/usr/bin/env python3
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Core library benchmarks for pyseq."""

import argparse
import json
import platform
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from pyseq import Sequence, get_sequences, uncompress
from pyseq import seq as pyseq
from pyseq.util import resolve_sequence_reference


PROFILE_CONFIG = {
    "smoke": {
        "iterations": 5,
        "sizes": [100, 1000, 10000],
        "mixed_factor": 2,
    },
    "full": {
        "iterations": 9,
        "sizes": [100, 1000, 10000],
        "mixed_factor": 3,
    },
}


def measure(func, iterations, warmups=1):
    """Return timing statistics for a benchmark callable."""
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


def contiguous_files(count):
    return [f"render.{frame:04d}.exr" for frame in range(1, count + 1)]


def mixed_files(count, factor):
    items = contiguous_files(count)
    extras = [f"note_{index:05d}.txt" for index in range(count * (factor - 1))]
    return sorted(items + extras)


def stepped_range_string(start, stop, step):
    return f"render.%04d.exr {start}-{stop}x{step}"


def run_profile(profile):
    config = PROFILE_CONFIG[profile]
    pyseq.strict_pad = False
    results = {}

    for size in config["sizes"]:
        results[f"sequence_construct_{size}"] = measure(
            lambda size=size: Sequence(contiguous_files(size)),
            config["iterations"],
        )

        results[f"get_sequences_mixed_{size}"] = measure(
            lambda size=size: get_sequences(mixed_files(size, config["mixed_factor"])),
            config["iterations"],
        )

        results[f"uncompress_range_{size}"] = measure(
            lambda size=size: uncompress(
                f"render.%04d.exr 1001-{1000 + size}", fmt="%h%p%t %r"
            ),
            config["iterations"],
        )

    results["format_missing_sparse_large"] = measure(
        lambda: get_sequences(["image-1.jpg", "image-1000.jpg", "image-50000000.jpg"])[
            0
        ].format("%M"),
        config["iterations"],
    )

    results["uncompress_stepped_10k"] = measure(
        lambda: uncompress(stepped_range_string(1001, 10000, 3), fmt="%h%p%t %x"),
        config["iterations"],
    )

    results["format_stepped_10k"] = measure(
        lambda: uncompress(
            stepped_range_string(1001, 10000, 3), fmt="%h%p%t %x"
        ).format("%x"),
        config["iterations"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for frame in (1001, 1004, 1007, 1010):
            (tmp / f"stepA.{frame:04d}.exr").write_text("frame\n")

        results["resolve_sequence_reference_stepped"] = measure(
            lambda: resolve_sequence_reference(
                str(tmp / "stepA.%04d.exr") + " 1001-1010x3"
            ),
            config["iterations"],
        )

    return results


def build_payload(profile):
    return {
        "kind": "core",
        "profile": profile,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "benchmarks": run_profile(profile),
    }


def write_summary(payload, stream):
    print(
        f"# pyseq core benchmarks ({payload['profile']})",
        file=stream,
    )
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
