#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2011-2015, Ryan Galloway (ryan@rsgalloway.com)
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
# -----------------------------------------------------------------------------

import os
import unittest
import subprocess
from pyseq import Item, Sequence, diff, uncompress, getSequences


class ItemTestCase(unittest.TestCase):
    """tests the Item class
    """

    def setUp(self):
        """set up the test
        """
        self.test_path = \
            '/mnt/S/Some/Path/to/a/file/with/numbers/file.0010.exr'

    def test_initializing_with_a_string(self):
        """testing if initializing an Item with a string showing the path of a
        file is working properly
        """
        i = Item(self.test_path)
        self.assertTrue(isinstance(i, Item))

    def test_path_attribute_is_working_properly(self):
        """testing if the path attribute is working properly
        """
        i = Item(self.test_path)
        self.assertEqual(
            self.test_path,
            i.path
        )

    def test_path_attribute_is_read_only(self):
        """testing if the path attribute is read only
        """
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, 'path', 'some value')

        self.assertEqual(
            str(cm.exception),
            "can't set attribute"
        )

    def test_name_attribute_is_working_properly(self):
        """testing if the name attribute is working properly
        """
        i = Item(self.test_path)
        self.assertEqual(
            i.name,
            'file.0010.exr'
        )

    def test_name_attribute_is_read_only(self):
        """testing if the name attribute is read only
        """
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, 'name', 'some value')

        self.assertEqual(
            str(cm.exception),
            "can't set attribute"
        )

    def test_dirname_attribute_is_working_properly(self):
        """testing if the dirname attribute is working properly
        """
        i = Item(self.test_path)
        self.assertEqual(
            i.dirname,
            '/mnt/S/Some/Path/to/a/file/with/numbers'
        )

    def test_dirname_attribute_is_read_only(self):
        """testing if the dirname attribute is read only
        """
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, 'dirname', 'some value')

        self.assertEqual(
            str(cm.exception),
            "can't set attribute"
        )

    def test_digits_attribute_is_working_properly(self):
        """testing if the digits attribute is working properly
        """
        i = Item(self.test_path)
        self.assertEqual(
            i.digits,
            ['0010']
        )

    def test_digits_attribute_is_read_only(self):
        """testing if the digits attribute is read only
        """
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, 'digits', 'some value')

        self.assertEqual(
            str(cm.exception),
            "can't set attribute"
        )

    def test_parts_attribute_is_working_properly(self):
        """testing if the parts attribute is working properly
        """
        i = Item(self.test_path)
        self.assertEqual(
            i.parts,
            ['file.', '.exr']
        )

    def test_parts_attribute_is_read_only(self):
        """testing if the parts attribute is read only
        """
        i = Item(self.test_path)
        with self.assertRaises(AttributeError) as cm:
            setattr(i, 'parts', 'some value')

        self.assertEqual(
            str(cm.exception),
            "can't set attribute"
        )

    def test_isSibling_method_is_working_properly(self):
        """testing if the is_sibling() is working properly
        """
        item1 = Item('/mnt/S/Some/Path/to/a/file/with/numbers/file.0010.exr')
        item2 = Item('/mnt/S/Some/Path/to/a/file/with/numbers/file.0101.exr')

        self.assertTrue(item1.isSibling(item2))
        self.assertTrue(item2.isSibling(item1))


class SequenceTestCase(unittest.TestCase):
    """tests the pyseq
    """

    def setUp(self):
        """set the test up
        """
        self.files = ['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg']

    def test_from_list(self):
        """testing if Sequence instance can be initialized with a list of file
        names
        """
        seq = Sequence(self.files)
        self.assertEqual(
            str(seq),
            'file.1-3.jpg'
        )

    def test_appending_a_new_file(self):
        """testing if it is possible to append a new item to the list by giving
        the file name
        """
        seq = Sequence(self.files)
        test_file = 'file.0006.jpg'
        seq.append(test_file)
        self.assertTrue(
            seq.contains('file.0005.jpg')
        )
        self.assertTrue(
            seq.contains(test_file)
        )
        self.assertFalse(
            seq.contains('file.0015.jpg')
        )

    def test_includes_is_working_properly(self):
        """testing if Sequence.includes() method is working properly
        """
        seq = Sequence(self.files)
        self.assertTrue(seq.includes('file.0009.jpg'))
        self.assertFalse(seq.includes('file.0009.pic'))

    def test_contains_is_working_properly(self):
        """testing if Sequence.contains() method is working properly
        """
        seq = Sequence(self.files)
        self.assertFalse(seq.contains('file.0009.jpg'))
        self.assertFalse(seq.contains('file.0009.pic'))

    def test_format_is_working_properly_1(self):
        """testing if format is working properly
        """
        seq = Sequence(self.files)
        seq.append('file.0006.jpg')
        self.assertEqual(
            seq.format('%h%p%t %r (%R)'),
            'file.%04d.jpg 1-6 (1-3 6)'
        )

    def test_format_is_working_properly_2(self):
        """testing if format is working properly
        """
        seq = Sequence(self.files)
        seq.append('file.0006.jpg')
        self.assertEqual(
            'file.0001-0006.jpg',
            seq.format('%h%04s-%04e%t'),
        )
        self.assertEqual(
            'file.   1-   6.jpg',
            seq.format('%h%4s-%4e%t'),
        )


class HelperFunctionsTestCase(unittest.TestCase):
    """tests the helper functions like
    pyseq.diff()
    pyseq.uncompress()
    pyseq.getSequences()
    """

    def test_diff_is_working_properly_1(self):
        """testing if diff is working properly
        """
        self.assertEqual(
            diff('file01_0040.rgb', 'file01_0041.rgb'),
            [{'frames': ('0040', '0041'), 'start': 7, 'end': 11}]
        )

    def test_diff_is_working_properly_2(self):
        """testing if diff is working properly
        """
        self.assertEqual(
            diff('file3.03.rgb', 'file4.03.rgb'),
            [{'frames': ('3', '4'), 'start': 4, 'end': 5}]
        )

    def test_uncompress_is_working_properly_1(self):
        """testing if uncompress is working properly
        """
        seq = uncompress(
            './tests/files/012_vb_110_v001.%04d.png 1-10',
            fmt='%h%p%t %r'
        )
        self.assertEqual(
            '012_vb_110_v001.1-10.png',
            str(seq)
        )

        self.assertEqual(10, len(seq))

    def test_uncompress_is_working_properly_2(self):
        """testing if uncompress is working properly
        """
        seq2 = uncompress(
            './tests/files/a.%03d.tga 1-3 10 12-14',
            fmt='%h%p%t %R'
        )
        self.assertEqual(
            'a.1-14.tga',
            str(seq2)
        )

        self.assertEqual(
            7,
            len(seq2)
        )

    def test_uncompress_is_working_properly_3(self):
        """testing if uncompress is working properly
        """
        seq3 = uncompress(
            'a.%03d.tga 1-14 (1-3 10 12-14)',
            fmt='%h%p%t %r (%R)'
        )
        self.assertEqual(
            'a.1-14.tga',
            str(seq3)
        )

        self.assertEqual(
            7,
            len(seq3)
        )

    def test_uncompress_is_working_properly_4(self):
        """testing if uncompress is working properly
        """
        seq4 = uncompress(
            'a.%03d.tga 1-14 (1-3 10 12-14)',
            fmt='%h%p%t %s-%e (%R)'
        )
        self.assertEqual(
            'a.1-14.tga',
            str(seq4)
        )

    def test_uncompress_is_working_properly_5(self):
        """testing if uncompress is working properly
        """
        seq5 = uncompress('a.%03d.tga 1-14 (1 14)', fmt='%h%p%t %r (%R)')
        self.assertEqual(
            'a.1-14.tga',
            str(seq5)
        )

        self.assertEqual(
            2,
            len(seq5)
        )

    def test_uncompress_is_working_properly_6(self):
        """testing if uncompress is working properly
        """
        seq6 = uncompress('a.%03d.tga 1-14 (1-14)', fmt='%h%p%t %r (%R)')
        self.assertEqual(
            'a.1-14.tga',
            str(seq6)
        )

        self.assertEqual(
            14,
            len(seq6)
        )

    def test_uncompress_is_working_properly_7(self):
        """testing if uncompress is working properly
        """
        seq7 = uncompress(
            'a.%03d.tga 1-100000 (1-10 100000)',
            fmt='%h%p%t %r (%R)'
        )
        self.assertEqual(
            'a.1-100000.tga',
            str(seq7)
        )

        self.assertEqual(
            11,
            len(seq7)
        )

    def test_uncompress_is_working_properly_8(self):
        """testing if uncompress is working properly
        """
        seq8 = uncompress(
            'a.%03d.tga 1-100 ([10, 20, 40, 50])',
            fmt='%h%p%t %r (%m)'
        )
        self.assertEqual(
            'a.1-100.tga',
            str(seq8)
        )

        self.assertEqual(
            96,
            len(seq8)
        )

    def test_getSequences_is_working_properly_1(self):
        """testing if getSequences is working properly
        """
        seqs = getSequences('./files/')

        expected_results = [
            '012_vb_110_v001.1-10.png',
            '012_vb_110_v002.1-10.png',
            'a.1-14.tga',
            'alpha.txt',
            'bnc01_TinkSO_tx_0_ty_0.101-105.tif',
            'bnc01_TinkSO_tx_0_ty_1.101-105.tif',
            'bnc01_TinkSO_tx_1_ty_0.101-105.tif',
            'bnc01_TinkSO_tx_1_ty_1.101-105.tif',
            'file.1-2.tif',
            'file.info.03.rgb',
            'file01_40-43.rgb',
            'file02_44-47.rgb',
            'file1-4.03.rgb',
            'fileA.1-3.jpg',
            'fileA.1-3.png',
            'file_02.tif',
            'z1_001_v1.1-4.png',
            'z1_002_v1.1-4.png',
            'z1_002_v2.1-4.png',
        ]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(
                expected_result,
                str(seq)
            )

    def test_getSequences_is_working_properly_2(self):
        """testing if getSequences is working properly
        """
        seqs = getSequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
        expected_results = [
            'fileA.1-2.rgb',
            'fileB.1.rgb'
        ]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(
                expected_result,
                str(seq)
            )

    def test_getSequences_is_working_properly_3(self):
        """testing if getSequences is working properly
        """
        seqs = getSequences('./tests/files/bnc*')
        expected_results = [
            'bnc01_TinkSO_tx_0_ty_0.%04d.tif 101-105',
            'bnc01_TinkSO_tx_0_ty_1.%04d.tif 101-105',
            'bnc01_TinkSO_tx_1_ty_0.%04d.tif 101-105',
            'bnc01_TinkSO_tx_1_ty_1.%04d.tif 101-105',
        ]
        for seq, expected_result in zip(seqs, expected_results):
            self.assertEqual(
                expected_result,
                seq.format('%h%p%t %r')
            )


class LSSTestCase(unittest.TestCase):
    """Tests lss command
    """

    def run_command(self, *args):
        """a simple wrapper for subprocess.Popen
        """
        process = subprocess.Popen(args, stdout=subprocess.PIPE)

        # loop until process finishes and capture stderr output
        stdout_buffer = []
        while True:
            stdout = process.stdout.readline()

            if stdout == b'' and process.poll() is not None:
                break

            if stdout != b'':
                stdout_buffer.append(stdout)

        # flatten the buffer
        return b''.join(stdout_buffer)

    def setUp(self):
        """
        """
        self.here = os.path.dirname(__file__)
        self.lss = os.path.join(os.path.dirname(self.here), 'lss')

    def test_lss_is_working_properly_1(self):
        """testing if the lss command is working properly
        """
        test_files = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "files"
        )

        result = self.run_command(
            self.lss,
            test_files
        )

        self.assertEqual(
            """  10 012_vb_110_v001.%04d.png 1-10
  10 012_vb_110_v002.%04d.png 1-10
   7 a.%03d.tga 1-3 10 12-14
   1 alpha.txt 
   5 bnc01_TinkSO_tx_0_ty_0.%04d.tif 101-105
   5 bnc01_TinkSO_tx_0_ty_1.%04d.tif 101-105
   5 bnc01_TinkSO_tx_1_ty_0.%04d.tif 101-105
   5 bnc01_TinkSO_tx_1_ty_1.%04d.tif 101-105
   2 file.%02d.tif 1-2
   1 file.info.03.rgb 
   4 file01_%04d.rgb 40-43
   4 file02_%04d.rgb 44-47
   4 file%d.03.rgb 1-4
   3 fileA.%04d.jpg 1-3
   3 fileA.%04d.png 1-3
   1 file_02.tif 
   4 z1_001_v1.%d.png 1-4
   4 z1_002_v1.%d.png 1-4
   4 z1_002_v2.%d.png 1-4
""",
            result
        )


if __name__ == '__main__':
    unittest.main()
