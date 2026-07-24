#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Frame range parsing and formatting helpers."""

from typing import List, Optional, Tuple

from pyseq import config


def has_serialized_range(text: str) -> bool:
    """Return True when text includes explicit serialized frame range syntax."""
    return bool(config.serialized_range_re.search(text))


def split_embedded_frame_range(text: str) -> Optional[Tuple[str, str, str]]:
    """Split `head<range>tail` strings like `plate.2-4.exr` into components."""
    match = config.embedded_range_re.match(text)
    if not match:
        return None
    return match.group("head"), match.group("range"), match.group("tail")


def parse_frame_range(range_text: str) -> List[int]:
    """Parse an extended frame range string into a list of frame numbers."""
    text = range_text.strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    if not text:
        return []

    frames = []
    for segment in text.split(","):
        segment = segment.strip()
        if not segment:
            raise ValueError(f"Invalid frame range syntax: {range_text}")
        match = config.frame_range_segment_re.match(segment)
        if not match:
            raise ValueError(f"Invalid frame range syntax: {segment}")

        start = int(match.group("start"))
        end = match.group("end")
        step = match.group("step")

        if start < 0 and not config.allow_negative_frames():
            raise ValueError(
                "Negative frame ranges require PYSEQ_ALLOW_NEGATIVE_FRAMES=1"
            )

        if end is None:
            frames.append(start)
            continue

        end = int(end)
        if end < 0 and not config.allow_negative_frames():
            raise ValueError(
                "Negative frame ranges require PYSEQ_ALLOW_NEGATIVE_FRAMES=1"
            )
        step = int(step) if step is not None else 1
        if step <= 0:
            raise ValueError(f"Frame step must be positive: {segment}")

        direction = 1 if end >= start else -1
        stop = end + direction
        frames.extend(range(start, stop, direction * step))

    return frames


def _frame_groups(frames: List[int]):
    """Return canonical arithmetic groups for a sorted frame list."""
    unique_frames = sorted(set(frames))
    if not unique_frames:
        return []
    if len(unique_frames) == 1:
        return [(unique_frames[0], unique_frames[0], None, 1)]

    groups = []
    start = unique_frames[0]
    prev = unique_frames[0]
    step = None
    count = 1

    for frame in unique_frames[1:]:
        diff = frame - prev
        if step is None:
            step = diff
            prev = frame
            count += 1
            continue
        if diff == step:
            prev = frame
            count += 1
            continue
        groups.append((start, prev, step, count))
        start = prev = frame
        step = None
        count = 1

    groups.append((start, prev, step, count))
    return groups


def format_frame_range_explicit(
    frames: List[int], pad_with_brackets: bool = True
) -> str:
    """Format frames as explicit contiguous segments."""
    if not frames:
        return ""

    frange = []
    start = end = None
    for frame in sorted(set(frames)):
        if start is None:
            start = end = frame
            continue
        if frame != end + 1:
            if start == end:
                frange.append(str(start))
            else:
                frange.append(f"{start}-{end}")
            start = end = frame
            continue
        end = frame

    if start is not None:
        if start == end:
            frange.append(str(start))
        else:
            frange.append(f"{start}-{end}")

    body = config.range_join.join(frange)
    return f"[{body}]" if pad_with_brackets else body


def format_frame_range_stepped(frames: List[int]) -> str:
    """Format frames using canonical stepped-range syntax."""
    if not frames:
        return ""

    parts = []
    for start, end, step, count in _frame_groups(frames):
        if count == 1:
            parts.append(str(start))
        elif step == 1:
            parts.append(f"{start}-{end}")
        elif count == 2:
            parts.extend([str(start), str(end)])
        else:
            parts.append(f"{start}-{end}x{step}")
    return ",".join(parts)
