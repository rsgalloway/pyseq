#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of the software nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

__doc__ = """
Contains tests for the pyseq package.
"""

import os
import re
import random
import unittest
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyseq import Item, Sequence, diff, uncompress, get_sequences
from pyseq import SequenceError
from pyseq import seq as pyseq

pyseq.default_format = "%h%r%t"


class ItemTestCase(unittest.TestCase):
    """tests the Item class"""

    def setUp(self):
        """set up the test"""
        self.test_path = os.path.abspath(
            os.path.join(
                os.sep,
                "mnt",
                "S",
                "Some",
                "Path",
                "to",
                "a",
                "file",
                "with",
                "numbers",
                "file.0010.exr",
            )
        )

    def test_initializing_with_a_string(self):
        """testing if initializing an Item with a string showing the path of a
        file is working properly
        """
        i = Item(self.test_path)
        self.assertTrue(isinstance(i, Item))

    def test_path_attribute_is_working_properly(self):
        """testing if the path attribute is working properly"""
        i = Item(self.test_path)
        self.assertEqual(self.test_path, i.path)

    def test_path_attribute_is_read_only(self):
        """testing if the path attribute is read only"""
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, "path", "some value")

        self.assertEqual(str(cm.exception), "can't set attribute")

    def test_name_attribute_is_working_properly(self):
        """testing if the name attribute is working properly"""
        i = Item(self.test_path)
        self.assertEqual(i.name, "file.0010.exr")

    def test_name_attribute_is_read_only(self):
        """testing if the name attribute is read only"""
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, "name", "some value")

        self.assertEqual(str(cm.exception), "can't set attribute")

    def test_dirname_attribute_is_working_properly(self):
        """testing if the dirname attribute is working properly"""

        i = Item(self.test_path)
        self.assertEqual(i.dirname, os.path.dirname(self.test_path))

    def test_dirname_attribute_is_read_only(self):
        """testing if the dirname attribute is read only"""
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, "dirname", "some value")

        self.assertEqual(str(cm.exception), "can't set attribute")

    def test_digits_attribute_is_working_properly(self):
        """testing if the digits attribute is working properly"""
        i = Item(self.test_path)
        self.assertEqual(i.digits, ["0010"])

    def test_digits_attribute_is_read_only(self):
        """testing if the digits attribute is read only"""
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, "digits", "some value")

        self.assertEqual(str(cm.exception), "can't set attribute")

    def test_parts_attribute_is_working_properly(self):
        """testing if the parts attribute is working properly"""
        i = Item(self.test_path)
        self.assertEqual(i.parts, ["file.", ".exr"])

    def test_parts_attribute_is_read_only(self):
        """testing if the parts attribute is read only"""
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, "parts", "some value")

        self.assertEqual(str(cm.exception), "can't set attribute")

    def test_is_sibling_method_is_working_properly(self):
        """testing if the is_sibling() is working properly"""
        item1 = Item("/mnt/S/Some/Path/to/a/file/with/numbers/file.0010.exr")
        item2 = Item("/mnt/S/Some/Path/to/a/file/with/numbers/file.0101.exr")

        self.assertTrue(item1.is_sibling(item2))
        self.assertTrue(item2.is_sibling(item1))


class SequenceTestCase(unittest.TestCase):
    """tests the pyseq"""

    def setUp(self):
        """set the test up"""
        self.files = ["file.0001.jpg", "file.0002.jpg", "file.0003.jpg"]

    def test_from_list(self):
        """testing if Sequence instance can be initialized with a list of file
        names
        """
        seq = Sequence(self.files)
        self.assertEqual(str(seq), "file.1-3.jpg")

    def test_appending_a_new_file(self):
        """testing if it is possible to append a new item to the list by giving
        the file name
        """
        seq = Sequence(self.files)
        test_file = "file.0006.jpg"
        seq.append(test_file)
        self.assertTrue(seq.contains("file.0005.jpg"))
        self.assertTrue(seq.contains(test_file))
        self.assertFalse(seq.contains("file.0015.jpg"))

    def test___setitem__(self):
        s = Sequence(["file.01.ext", "file.05.ext"])
        s[1] = "file.02.ext"
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.01.ext"))
        self.assertEqual(s[1], Item("file.02.ext"))

        self.assertRaises(SequenceError, s.__setitem__, 0, "item.1.ext")

    def test___add__(self):
        s = Sequence(["file.01.ext"])
        ns = s + Item("file.02.ext")
        self.assertEqual(len(ns), 2)
        self.assertEqual(ns[0], s[0])
        self.assertEqual(ns[1], Item("file.02.ext"))
        self.assertEqual(len(s), 1)

        ns = s + "file.02.ext"
        self.assertEqual(len(ns), 2)
        self.assertEqual(ns[0], s[0])
        self.assertEqual(ns[1], Item("file.02.ext"))
        self.assertEqual(len(s), 1)

        ns = s + ["file.02.ext"]
        self.assertEqual(len(ns), 2)
        self.assertEqual(ns[0], s[0])
        self.assertEqual(ns[1], Item("file.02.ext"))
        self.assertEqual(len(s), 1)

        ns = s + Sequence(["file.02.ext"])
        self.assertEqual(len(ns), 2)
        self.assertEqual(ns[0], s[0])
        self.assertEqual(ns[1], Item("file.02.ext"))
        self.assertEqual(len(s), 1)

        self.assertRaises(SequenceError, s.__add__, "item.01.ext")
        self.assertRaises(TypeError, s.__add__, 1)

    def test___iadd__(self):
        s = Sequence(["file.01.ext"])
        s += Item("file.02.ext")
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], s[0])
        self.assertEqual(s[1], Item("file.02.ext"))

        s = Sequence(["file.01.ext"])
        s += "file.02.ext"
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], s[0])
        self.assertEqual(s[1], Item("file.02.ext"))

        s = Sequence(["file.01.ext"])
        s += ["file.02.ext"]
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], s[0])
        self.assertEqual(s[1], Item("file.02.ext"))

        s = Sequence(["file.01.ext"])
        s += Sequence(["file.02.ext"])
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], s[0])
        self.assertEqual(s[1], Item("file.02.ext"))

    def test___setslice___(self):
        s = Sequence(["file.001.ext"])
        s[1:2] = "file.002.ext"
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.001.ext"))
        self.assertEqual(s[1], Item("file.002.ext"))

        s = Sequence(["file.001.ext"])
        s[1:2] = Item("file.002.ext")
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.001.ext"))
        self.assertEqual(s[1], Item("file.002.ext"))

        s = Sequence(["file.001.ext"])
        s[1:2] = [Item("file.002.ext")]
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.001.ext"))
        self.assertEqual(s[1], Item("file.002.ext"))

        s = Sequence(["file.001.ext"])
        s[1:2] = Sequence([Item("file.002.ext")])
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.001.ext"))
        self.assertEqual(s[1], Item("file.002.ext"))

        self.assertRaises(SequenceError, s.__setslice__, 1, 2, "item.001.ext")

    def test_insert(self):
        s = Sequence(["file.001.ext"])
        s.insert(0, "file.002.ext")
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], Item("file.002.ext"))
        self.assertEqual(s[1], Item("file.001.ext"))

        self.assertRaises(SequenceError, s.insert, 1, "item")

    def test_extend(self):
        s = Sequence(["file.001.ext"])
        s.extend(["file.002.ext", "file.003.ext"])
        self.assertEqual(len(s), 3)
        self.assertEqual(s[0], Item("file.001.ext"))
        self.assertEqual(s[1], Item("file.002.ext"))
        self.assertEqual(s[2], Item("file.003.ext"))

        self.assertRaises(SequenceError, s.extend, ["item"])

    def test_includes_is_working_properly(self):
        """testing if Sequence.includes() method is working properly"""
        seq = Sequence(self.files)
        self.assertTrue(seq.includes("file.0009.jpg"))
        self.assertFalse(seq.includes("file.0009.pic"))

    def test_contains_is_working_properly(self):
        """test if Sequence.contains() method is working properly"""
        seq = Sequence(self.files)
        self.assertFalse(seq.contains("file.0009.jpg"))
        self.assertFalse(seq.contains("file.0009.pic"))

    def test_format_is_working_properly_1(self):
        """test if format is working properly"""
        seq = Sequence(self.files)
        seq.append("file.0006.jpg")
        self.assertEqual(seq.format("%h%p%t %r (%R)"), "file.%04d.jpg 1-6 ([1-3, 6])")

    def test_format_is_working_properly_2(self):
        """test if format is working properly"""
        seq = Sequence(self.files)
        seq.append("file.0006.jpg")
        self.assertEqual(
            "file.0001-0006.jpg",
            seq.format("%h%04s-%04e%t"),
        )
        self.assertEqual(
            "file.   1-   6.jpg",
            seq.format("%h%4s-%4e%t"),
        )

    def test_format_is_working_properly_3(self):
        """test if format is working properly"""
        seq = Sequence(self.files)
        seq.append("file.0006.jpg")
        seq.append("file.0010.jpg")
        self.assertEqual(
            seq.format("%h%p%t %r (missing %M)"),
            "file.%04d.jpg 1-10 (missing [4-5, 7-9])",
        )

    def test_format_directory_attribute(self):
        dir_name = os.path.dirname(self.files[0]) + os.sep
        seq = Sequence(self.files)
        self.assertEqual(seq.format("%D"), dir_name)

    def test__get_missing(self):
        """test that _get_missing works"""
        # Can't initialize Sequence without an item
        # seq = Sequence([])
        # self.assertEqual(seq._get_missing(), [])

        seq = Sequence(["file.00010.jpg"])
        self.assertEqual(seq._get_missing(), [])

        seq = Sequence(self.files)
        seq.append("file.0006.jpg")
        self.assertEqual(seq._get_missing(), [4, 5])

        seq = Sequence(["file.%04d.jpg" % i for i in range(20)])
        seq.pop(10)
        seq.pop(10)
        seq.pop(10)
        seq.pop(14)
        seq.pop(14)
        missing = [10, 11, 12, 17, 18]
        self.assertEqual(seq._get_missing(), missing)

        missing = []
        seq = Sequence(["file.0001.jpg"])
        for i in range(2, 50):
            if random.randint(0, 1) == 1:
                seq.append("file.%04d.jpg" % i)
            else:
                missing.append(i)

        # remove ending random frames
        while missing[-1] > int(re.search(r"file\.(\d{4})\.jpg", seq[-1]).group(1)):
            missing.pop(-1)
        self.assertEqual(seq._get_missing(), missing)


class PadSizeTestCase(unittest.TestCase):
    def test_padsize_with_default_padding(self):
        item = Item("file.001.exr")
        frame = "001"
        expected_padsize = 3

        result = pyseq.padsize(item, frame)

        self.assertEqual(result, expected_padsize)

    def test_padsize_with_custom_padding(self):
        item = Item("file.001001.exr")
        frame = "001001"
        expected_padsize = 6

        result = pyseq.padsize(item, frame)

        self.assertEqual(result, expected_padsize)

    def test_padsize_with_no_padding(self):
        item = Item("file.9.jpg")
        frame = "9"
        expected_padsize = 0

        result = pyseq.padsize(item, frame)

        self.assertEqual(result, expected_padsize)

    def test_padsize_with_strict_padding_disabled(self):
        pyseq.strict_pad = False
        item = Item("file.9.jpg")
        frame = "9"
        expected_padsize = 0

        result = pyseq.padsize(item, frame)

        self.assertEqual(result, expected_padsize)

    def test_padsize_with_strict_padding_enabled(self):
        pyseq.strict_pad = True
        item = Item("file.09.jpg")
        frame = "09"
        expected_padsize = 2

        result = pyseq.padsize(item, frame)

        self.assertEqual(result, expected_padsize)


class HelperFunctionsTestCase(unittest.TestCase):
    """tests the helper functions like
    pyseq.diff()
    pyseq.uncompress()
    pyseq.get_sequences()
    """

    def test_diff_is_working_properly_1(self):
        """testing if diff is working properly"""
        self.assertEqual(
            diff("file01_0040.rgb", "file01_0041.rgb"),
            [{"frames": ("0040", "0041"), "start": 7, "end": 11}],
        )

    def test_diff_is_working_properly_2(self):
        """testing if diff is working properly"""
        self.assertEqual(
            diff("file3.03.rgb", "file4.03.rgb"),
            [{"frames": ("3", "4"), "start": 4, "end": 5}],
        )

    def test_uncompress_is_working_properly_1(self):
        """testing if uncompress is working properly"""
        seq = uncompress("./tests/files/012_vb_110_v001.%04d.png 1-10", fmt="%h%p%t %r")
        self.assertEqual("012_vb_110_v001.1-10.png", str(seq))

        self.assertEqual(10, len(seq))

    def test_uncompress_is_working_properly_2(self):
        """testing if uncompress is working properly"""
        seq2 = uncompress("./tests/files/a.%03d.tga [1-3, 10, 12-14]", fmt="%h%p%t %R")
        self.assertEqual("a.1-14.tga", str(seq2))

        self.assertEqual(7, len(seq2))

    def test_uncompress_is_working_properly_3(self):
        """testing if uncompress is working properly"""
        seq3 = uncompress("a.%03d.tga 1-14 ([1-3, 10, 12-14])", fmt="%h%p%t %r (%R)")
        self.assertEqual("a.1-14.tga", str(seq3))

        self.assertEqual(7, len(seq3))

    def test_uncompress_is_working_properly_4(self):
        """testing if uncompress is working properly"""
        seq4 = uncompress("a.%03d.tga 1-14 ([1-3, 10, 12-14])", fmt="%h%p%t %s-%e (%R)")
        self.assertEqual("a.1-14.tga", str(seq4))

    def test_uncompress_is_working_properly_5(self):
        """testing if uncompress is working properly"""
        seq5 = uncompress("a.%03d.tga 1-14 [1-14]", fmt="%h%p%t %r %R")
        self.assertEqual("a.1-14.tga", str(seq5))

        self.assertEqual(14, len(seq5))

    def test_uncompress_is_working_properly_6(self):
        """testing if uncompress is working properly"""
        seq6 = uncompress("a.%03d.tga 1-14 ([1-14])", fmt="%h%p%t %r (%R)")
        self.assertEqual("a.1-14.tga", str(seq6))

        self.assertEqual(14, len(seq6))

    def test_uncompress_is_working_properly_7(self):
        """testing if uncompress is working properly,
        the frame 100000 does not fit inside the pad length
        """

        # enable strict pad checking
        pyseq.strict_pad = True

        seq7 = uncompress("a.%03d.tga 1-100000 ([1-10, 100000])", fmt="%h%p%t %r (%R)")
        self.assertEqual("a.1-10.tga", str(seq7))

        self.assertEqual(10, len(seq7))

        # disable strict pad checking
        pyseq.strict_pad = False

        seq7 = uncompress("a.%03d.tga 1-100000 ([1-10, 100000])", fmt="%h%p%t %r (%R)")
        self.assertEqual("a.1-100000.tga", str(seq7))

        self.assertEqual(11, len(seq7))

    def test_uncompress_is_working_properly_8(self):
        """testing if uncompress is working properly"""
        seq8 = uncompress("a.%03d.tga 1-100 ([10, 20, 40, 50])", fmt="%h%p%t %r (%m)")
        self.assertEqual("a.1-100.tga", str(seq8))

        self.assertEqual(96, len(seq8))

    def test_get_sequences_is_working_properly_1(self):
        """testing if get_sequences is working properly"""
        seqs = get_sequences("./files/")

        expected_results = [
            "012_vb_110_v001.1-10.png",
            "012_vb_110_v002.1-10.png",
            "a.1-14.tga",
            "alpha.txt",
            "bnc01_TinkSO_tx_0_ty_0.101-105.tif",
            "bnc01_TinkSO_tx_0_ty_1.101-105.tif",
            "bnc01_TinkSO_tx_1_ty_0.101-105.tif",
            "bnc01_TinkSO_tx_1_ty_1.101-105.tif",
            "file.1-2.tif",
            "file.info.03.rgb",
            "file01.1-4.j2k",
            "file01_40-43.rgb",
            "file02_44-47.rgb",
            "file1-4.03.rgb",
            "fileA.1-3.jpg",
            "fileA.1-3.png",
            "file_02.tif",
            "z1_001_v1.1-4.png",
            "z1_002_v1.1-4.png",
            "z1_002_v2.1-4.png",
        ]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(expected_result, str(seq))

    def test_get_sequences_is_working_properly_2(self):
        """testing if get_sequences is working properly"""
        seqs = get_sequences(["fileA.1.rgb", "fileA.2.rgb", "fileB.1.rgb"])
        expected_results = ["fileA.1-2.rgb", "fileB.1.rgb"]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(expected_result, str(seq))

    def test_get_sequences_is_working_properly_3(self):
        """testing if get_sequences is working properly"""
        seqs = get_sequences("./tests/files/bnc*")
        expected_results = [
            "bnc01_TinkSO_tx_0_ty_0.%04d.tif 101-105",
            "bnc01_TinkSO_tx_0_ty_1.%04d.tif 101-105",
            "bnc01_TinkSO_tx_1_ty_0.%04d.tif 101-105",
            "bnc01_TinkSO_tx_1_ty_1.%04d.tif 101-105",
        ]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(expected_result, seq.format("%h%p%t %r"))


class LSSTestCase(unittest.TestCase):
    """Tests lss command"""

    def run_command(self, *args):
        """a simple wrapper for subprocess.Popen"""
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, universal_newlines=True
        )
        stdout, _ = process.communicate()
        return stdout

    def setUp(self):
        """ """
        self.maxDiff = None
        self.here = os.path.dirname(__file__)
        self.lss = os.path.realpath(
            os.path.join(os.path.dirname(self.here), "lib", "pyseq", "lss.py")
        )

    def test_lss_is_working_properly_1(self):
        """testing if the lss command is working properly. Assumes strict pad
        is disabled."""
        test_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), "files")

        result = self.run_command(self.lss, test_files)

        self.assertEqual(
            """  10 012_vb_110_v001.%04d.png [1-10]
  10 012_vb_110_v002.%04d.png [1-10]
   7 a.%03d.tga [1-3, 10, 12-14]
   1 alpha.txt 
   5 bnc01_TinkSO_tx_0_ty_0.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_0_ty_1.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_1_ty_0.%04d.tif [101-105]
   5 bnc01_TinkSO_tx_1_ty_1.%04d.tif [101-105]
   4 file.%02d.tif [1-2, 98-99]
   1 file.info.03.rgb 
   3 file01.%03d.j2k [1-2, 4]
   4 file01_%04d.rgb [40-43]
   4 file02_%04d.rgb [44-47]
   4 file%d.03.rgb [1-4]
   3 fileA.%04d.jpg [1-3]
   3 fileA.%04d.png [1-3]
   1 file_02.tif 
   4 z1_001_v1.%d.png [1-4]
   4 z1_002_v1.%d.png [1-4]
   4 z1_002_v2.%d.png [9-12]
""",
            result,
        )


class PerformanceTests(unittest.TestCase):
    """tests the performance of pyseq"""

    def test_performance_1(self):
        """tests performance for single 10k frame sequence"""
        files = ["file.%03d.jpg" % i for i in range(1, 10000)]
        s = time.time()
        seq = Sequence(files)
        e = time.time()
        total_time = e - s
        print("time taken to create sequence: %s" % (total_time))
        self.assertEqual(str(seq), "file.1-9999.jpg")
        self.assertEqual(len(seq), 9999)
        self.assertTrue(total_time < 0.1)


class TestIssues(unittest.TestCase):
    """tests reported issues on github"""

    def test_issue_60(self):
        """tests issue 60. with strict padding disabled,
        padding should be %d"""

        # disable strict padding
        pyseq.strict_pad = False

        items = [
            "file.7.jpg",
            "file.8.jpg",
            "file.9.jpg",
            "file.10.jpg",
            "file.11.jpg",
            "file.12.jpg",
            "file.87.jpg",
            "file.99.jpg",
            "file.111.jpg",
        ]
        seq = pyseq.get_sequences(items)[0]
        self.assertEqual(len(items), len(seq))
        self.assertEqual(seq._get_padding(), "%d")

        items = [
            "file.7.jpg",
            "file.8.jpg",
            "file.9.jpg",
            "file.10.jpg",
            "file.11.jpg",
            "file.12.jpg",
        ]
        seq = pyseq.get_sequences(items)[0]
        self.assertEqual(len(items), len(seq))
        self.assertEqual(seq._get_padding(), "%d")

        seq = pyseq.get_sequences(
            [
                "file.1.jpg",
                "file.100.jpg",
                "file.101.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 3)
        self.assertEqual(seq._get_padding(), "%d")

        seq = pyseq.get_sequences(
            [
                "file.10.jpg",
                "file.11.jpg",
                "file.12.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 3)
        self.assertEqual(seq._get_padding(), "%d")

        seq = pyseq.get_sequences(
            [
                "file.100.jpg",
                "file.101.jpg",
                "file.102.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 3)
        self.assertEqual(seq._get_padding(), "%d")

        seq = pyseq.get_sequences(
            [
                "file.9.jpg",
                "file.99.jpg",
                "file.999.jpg",
                "file.9999.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 4)
        self.assertEqual(seq._get_padding(), "%d")

        seq = pyseq.get_sequences(
            [
                "file.007.jpg",
                "file.010.jpg",
                "file.101.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 3)
        self.assertEqual(seq._get_padding(), "%03d")

        # revert to strict
        pyseq.strict_pad = True

        seq = pyseq.get_sequences(
            [
                "file.007.jpg",
                "file.010.jpg",
                "file.101.jpg",
            ]
        )[0]
        self.assertEqual(len(seq), 3)
        self.assertEqual(seq._get_padding(), "%03d")

    def test_issue_67(self):
        """tests issue 67. hangs on many of missing frames."""

        def get_range(frames):
            return range(frames[0], frames[-1] + 1)

        # test with strict padding disabled
        pyseq.strict_pad = False

        # normal test case (missing frame count w/i tolerance)
        files = [
            "image-1.jpg",
            "image-383.jpg",
            "image-844.jpg",
            "image-2500.jpg",
            "image-4529.jpg",
            "image-5000.jpg",
        ]

        seqs = get_sequences(files)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(len(seqs[0]), len(files))

        frames = seqs[0].frames()
        missing = seqs[0]._get_missing()
        self.assertEqual(len(frames), len(files))
        self.assertEqual(len(missing), 5000 - len(files))

        # high missing frame count test 1
        files = ["image-1.jpg", "image-1000.jpg", "image-50000000.jpg"]

        seqs = get_sequences(files)
        self.assertEqual(len(seqs), 1)

        frames = seqs[0].frames()
        missing = seqs[0]._get_missing()

        self.assertEqual(len(frames), len(files))
        r = get_range(frames)
        self.assertEqual(len(r), 50000000)
        self.assertTrue(len(missing), 2)  # <-- diff behavior: len is num. ranges
        self.assertEqual(missing[0][0], 2)
        self.assertEqual(missing[0][-1], 999)
        self.assertEqual(missing[1][0], 1001)
        self.assertEqual(missing[1][-1], 49999999)
        self.assertEqual(seqs[0].format(), "   3 image-%d.jpg [1, 1000, 50000000]")
        self.assertEqual(seqs[0].format("%M"), "[2-999, 1001-49999999, ]")

        # test with strict padding enabled
        pyseq.strict_pad = True

        # high missing frame count test 2
        files = ["image-100000000-2048x2048.jpg", "image-500000000-2048x2048.jpg"]

        seqs = get_sequences(files)
        self.assertEqual(len(seqs), 1)

        frames = seqs[0].frames()
        self.assertEqual(len(frames), 2)

        r = get_range(frames)
        self.assertEqual(len(r), 400000001)
        missing = seqs[0]._get_missing()
        self.assertTrue(len(missing), 5000000)
        self.assertEqual(missing[0][0], 100000001)
        self.assertEqual(missing[0][-1], 499999999)
        self.assertEqual(
            seqs[0].format(), "   2 image-%09d-2048x2048.jpg [100000000, 500000000]"
        )
        self.assertEqual(seqs[0].format("%M"), "[100000001-499999999, ]")

        # high missing frame count test 3 (from the issue)
        files = [
            "file-1364769281-2048x2048.jpg",
            "file-530573048-2048x2048.jpg",
            "file-1127718214-2048x2048.jpg",
            "file-470543560-2048x2048.jpg",
            "file-155374807-2048x2048.jpg",
            "file-1182189546-2048x2048.jpg",
            "file-157742535-2048x2048.jpg",
        ]

        seqs = get_sequences(files)
        self.assertEqual(len(seqs), 2)

        # files with frame padding=10
        self.assertEqual(seqs[0].frames(), [1127718214, 1182189546, 1364769281])

        # frame ranges are in the millions
        frames = seqs[0].frames()
        r = get_range(frames)
        self.assertEqual(len(r), 237051068)

        frames = seqs[1].frames()
        r = get_range(frames)
        self.assertEqual(len(r), 375198242)

        # files with frame padding=9
        self.assertEqual(seqs[1].frames(), [155374807, 157742535, 470543560, 530573048])

    def test_issue_69(self):
        """tests issue 69. more strict padding tests."""

        # padded frames
        padded = [
            "file.08.jpg",
            "file.09.jpg",
            "file.10.jpg",
            "file.11.jpg",
        ]

        # unpadded frames
        unpadded = [
            "file.8.jpg",
            "file.9.jpg",
            "file.10.jpg",
            "file.11.jpg",
        ]

        seqformat = "%4l %h%p%t %R"

        # test with strict padding enabled (default)
        # with strict pad enabled, the num of digits in each frame must match
        pyseq.strict_pad = True

        # test padded frames
        seqs = get_sequences(padded)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(seqs[0].format(seqformat), "   4 file.%02d.jpg [8-11]")

        # test unpadded frames
        seqs = get_sequences(unpadded)
        self.assertEqual(len(seqs), 2)
        self.assertEqual(seqs[0].format(seqformat), "   2 file.%02d.jpg [10-11]")
        self.assertEqual(seqs[1].format(seqformat), "   2 file.%d.jpg [8-9]")

        # test uncompress with strict pad
        # finds frames 1-9 because num digits changes after 9
        s = uncompress("file.1-150.jpg", fmt="%h%r%t")
        self.assertEqual(len(s), 9)

        # test with strict padding disabled
        # with strict pad disabled, the num of digits in each frame can vary
        pyseq.strict_pad = False

        # test padded frames
        seqs = get_sequences(padded)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(seqs[0].format(seqformat), "   4 file.%02d.jpg [8-11]")

        # test unpadded frames
        seqs = get_sequences(unpadded)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(seqs[0].format(seqformat), "   4 file.%d.jpg [8-11]")

        # test uncompress without strict pad, finds all 150 frames
        s = uncompress("file.1-150.jpg", fmt="%h%r%t")
        self.assertEqual(len(s), 150)

    def test_issue_83(self):
        """tests issue 83. externalize frame pattern."""

        from pyseq import config

        filenames = [
            "file_v001.jpg",
            "file_v002.jpg",
            "file_v003.jpg",
            "file_v004.jpg",
        ]

        # test using default frame pattern
        seqs1 = pyseq.get_sequences(
            filenames, frame_pattern=config.DEFAULT_FRAME_PATTERN
        )
        self.assertEqual(len(seqs1), 1)

        # test if a new file in the sequence is included
        item = Item("file_v005.jpg")
        self.assertTrue(seqs1[0].includes(item))

        # test using custom frame pattern, different from first sequence
        seqs2 = pyseq.get_sequences(filenames, frame_pattern="_%d")

        # should have 4 sequences, with one file each
        self.assertEqual(len(seqs2), len(filenames))

        # test that items from sequences 1 and 2 are not siblings
        seq1item1 = seqs1[0][0]
        seq2item1 = seqs2[0][0]
        self.assertFalse(seq1item1.is_sibling(seq2item1))

        # test that 2 items in the sequence 1 are still siblings
        seq1item2 = seqs1[0][1]
        self.assertTrue(seq1item1.is_sibling(seq1item2))

        # test items in sequences 1 and 2 are not siblings
        self.assertFalse(seq1item1.is_sibling(seq2item1))

        # test that the new item is still included in the first sequence,
        # and excluded from the second sequence
        self.assertTrue(seqs1[0].includes(item))
        self.assertFalse(seqs2[0].includes(item))

    def test_issue_86(self):
        """tests issue 86. uncompress() with whitespace."""

        # test sequence with whitespace
        sequence_path = "path/to/file/image ([1-2, 4]).png"
        sequence = pyseq.uncompress(sequence_path, fmt="%h%R%t")
        self.assertEqual(str(sequence), "image (1-4).png")
        self.assertEqual(len(sequence), 3)
        self.assertEqual(sequence[0].path, "path/to/file/image (1).png")
        self.assertEqual(sequence[1].path, "path/to/file/image (2).png")
        self.assertEqual(sequence[2].path, "path/to/file/image (4).png")

        # test sequence with multiple spaces
        sequence_path = "other/path/file with spaces [10-40].png"
        sequence = pyseq.uncompress(sequence_path, fmt="%h%R%t")
        self.assertEqual(str(sequence), "file with spaces 10-40.png")
        self.assertEqual(len(sequence), 31)

        # test sequence with brackets
        sequence_path = "My file [v2].[1-2].jpg"
        sequence = pyseq.uncompress(sequence_path, fmt="%h%R%t")
        self.assertEqual(str(sequence), "My file [v2].1-2.jpg")
        self.assertEqual(len(sequence), 2)


if __name__ == "__main__":
    unittest.main()
