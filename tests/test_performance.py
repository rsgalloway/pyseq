#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#

"""Performance regression tests for pyseq."""

import time
import unittest

from pyseq import Sequence, get_sequences
from pyseq import seq as pyseq
from pyseq import uncompress


class PerformanceTests(unittest.TestCase):
    """Coarse-grained performance regression tests."""

    def test_sequence_construction_10k_frames(self):
        """Single large contiguous sequences should remain fast."""
        pyseq.strict_pad = False
        files = ["file.%03d.jpg" % i for i in range(1, 10000)]

        start = time.perf_counter()
        seq = Sequence(files)
        elapsed = time.perf_counter() - start

        self.assertEqual(str(seq), "file.1-9999.jpg")
        self.assertEqual(len(seq), 9999)
        self.assertLess(elapsed, 0.5)

    def test_sparse_large_missing_range(self):
        """Sparse huge ranges should not trigger catastrophic expansion."""
        pyseq.strict_pad = False
        files = ["image-1.jpg", "image-1000.jpg", "image-50000000.jpg"]

        start = time.perf_counter()
        seq = get_sequences(files)[0]
        missing = seq._get_missing()
        formatted = seq.format("%M")
        elapsed = time.perf_counter() - start

        self.assertEqual(seq.frames(), [1, 1000, 50000000])
        self.assertEqual(len(missing), 2)
        self.assertEqual(formatted, "[2-999, 1001-49999999, ]")
        # Keep this intentionally loose so we catch catastrophic regressions
        # without making CI timing-sensitive.
        self.assertLess(elapsed, 1.0)

    def test_stepped_range_parse_and_format(self):
        """Medium-sized stepped ranges should parse and format quickly."""
        pyseq.strict_pad = False

        start = time.perf_counter()
        seq = uncompress("render.%04d.exr 1001-10000x3", fmt="%h%p%t %x")
        rendered = seq.format("%x")
        elapsed = time.perf_counter() - start

        self.assertEqual(seq.frames()[0], 1001)
        self.assertEqual(seq.frames()[-1], 9998)
        self.assertEqual(rendered, "1001-9998x3")
        self.assertLess(elapsed, 0.5)


if __name__ == "__main__":
    unittest.main()
