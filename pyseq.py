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
"""docs and latest version available for download at
   http://github.com/rsgalloway/pyseq
"""

__version__ = "0.4.0"


import os
import re
import logging
from glob import glob
from datetime import datetime

# default serialization format string
gFormat = '%4l %h%p%t %R'

# regex for matching numerical characters
gDigitsRE = re.compile(r'\d+')

# regex for matching format directives
gFormatRE = re.compile(r'%(?P<pad>\d+)?(?P<var>\w+)')

__all__ = [
    'SequenceError', 'Item', 'Sequence', 'diff', 'uncompress', 'getSequences'
]

# logging handlers
log = logging.getLogger('pyseq')
log.addHandler(logging.StreamHandler())
log.setLevel(int(os.environ.get('PYSEQ_LOG_LEVEL', logging.INFO)))

# log.setLevel(logging.DEBUG)


class SequenceError(Exception):
    """special exception for sequence errors
    """
    pass


class FormatError(Exception):
    """special exception for seq format errors
    """
    pass


class Item(str):
    """Sequence member file class

    :param item: Path to file.
    """

    def __init__(self, item):
        super(Item, self).__init__()
        log.debug('adding %s' % item)
        self.item = item
        self.__path = getattr(item, 'path', os.path.abspath(str(item)))
        self.__dirname = os.path.dirname(str(item))
        self.__filename = os.path.basename(str(item))
        self.__digits = gDigitsRE.findall(self.name)
        self.__parts = gDigitsRE.split(self.name)
        
        if os.path.isfile(self.__path):
            self.__size = os.path.getsize(self.__path)
            self.__mtime = os.path.getmtime(self.__path)
        else:
            self.__size = 0
            self.__mtime = 0
        # modified by self.is_sibling()
        self.frame = ''
        self.head = self.name
        self.tail = ''

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return '<pyseq.Item "%s">' % self.name

    def __getattr__(self, key):
        return getattr(self.item, key, None)

    @property
    def path(self):
        """Item absolute path, if a filesystem item.
        """
        return self.__path


    @property
    def name(self):
        """Item base name attribute
        """
        return self.__filename

    @property
    def dirname(self):
        """"Item directory name, if a filesystem item."
        """
        return self.__dirname

    @property
    def digits(self):
        """Numerical components of item name.
        """
        return self.__digits

    @property
    def parts(self):
        """Non-numerical components of item name
        """
        return self.__parts

    @property
    def size(self):
        """Non-numerical components of item name
        """
        return self.__size

    @property
    def mtime(self):
        """Non-numerical components of item name
        """
        return self.__mtime

    def isSibling(self, item):
        """Determines if this and item are part of the same sequence.

        :param item: An :class:`.Item` instance.

        :return: True if this and item are sequential siblings.
        """
        if not isinstance(item, Item):
            item = Item(item)

        d = diff(self, item)
        is_sibling = (len(d) == 1) and (self.parts == item.parts)

        # I do not understand why we are updating information
        # while this is a predicate method
        if is_sibling:
            self.frame = d[0]['frames'][0]
            self.head = self.name[:d[0]['start']]
            self.tail = self.name[d[0]['end']:]
            item.frame = d[0]['frames'][1]
            item.head = item.name[:d[0]['start']]
            item.tail = item.name[d[0]['end']:]

        return is_sibling


class Sequence(list):
    """
    Extends list class with methods that handle item sequentialness.

    For example:

        >>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
        >>> print(s)
        file.1-3.jpg
        >>> s.append('file.0006.jpg')
        >>> print(s.format('%4l %h%p%t %R'))
           4 file.%04d.jpg 1-3 6
        >>> s.includes('file.0009.jpg')
        True
        >>> s.includes('file.0009.pic')
        False
        >>> s.contains('file.0006.jpg')
        False
        >>> print(s.format('%h%p%t %r (%R)'))
        file.%04d.jpg 1-6 (1-3 6)
    """

    def __init__(self, items):
        """
        Create a new Sequence class object.

        :param: items: Sequential list of items.

        :return: pyseq.Sequence class instance.
        """
        super(Sequence, self).__init__([Item(items.pop(0))])
        self.__missing = []
        self.__NEEDREINDEX = False
        while items:
            f = Item(items.pop(0))
            try:
                self.append(f)
                log.debug('+Item belongs to sequence.')
            except SequenceError:
                log.debug('-Item does not belong to sequence.')
                continue
            except KeyboardInterrupt:
                log.info("Stopping.")
                break
            
            

    def __attrs__(self):
        """Replaces format directives with values"""
        return {
            'l': self.length(),
            's': self.start(),
            'e': self.end(),
            'f': self.frames(),
            'm': self.missing(),
            'p': self._get_padding(),
            'r': self._get_framerange(missing=False),
            'R': self._get_framerange(missing=True),
            'h': self.head(),
            't': self.tail()
        }

    def __str__(self):
        return self.format('%h%r%t')

    def __repr__(self):
        return '<pyseq.Sequence "%s">' % str(self)

    def __getattr__(self, key):
        return getattr(self[0], key, None)

    def __contains__(self, item):
        super(Sequence, self).__contains__(Item(item))

    def format(self, fmt=gFormat):
        """Format the stdout string.

        The following directives can be embedded in the format string.
        Format directives support padding, for example: "%04l".

        +-----------+-------------------------------------+
        | Directive | Meaning                             |
        +===========+=====================================+
        | ``%s``    | sequence start                      |
        +-----------+-------------------------------------+
        | ``%e``    | sequence end                        |
        +-----------+-------------------------------------+
        | ``%l``    | sequence length                     |
        +-----------+-------------------------------------+
        | ``%f``    | list of found files                 |
        +-----------+-------------------------------------+
        | ``%m``    | list of missing files               |
        +-----------+-------------------------------------+
        | ``%p``    | padding, e.g. %06d                  |
        +-----------+-------------------------------------+
        | ``%r``    | implied range, start-end            |
        +-----------+-------------------------------------+
        | ``%R``    | explicit range, start-end [missing] |
        +-----------+-------------------------------------+
        | ``%h``    | string preceding sequence number    |
        +-----------+-------------------------------------+
        | ``%t``    | string after the sequence number    |
        +-----------+-------------------------------------+

        :param fmt: Format string. Default is '%4l %h%p%t %R'.

        :return: Formatted string.
        """
        
        format_char_types = {
            's': 'i',
            'e': 'i',
            'l': 'i',
            'f': 's',
            'm': 's',
            'p': 's',
            'r': 's',
            'R': 's',
            'h': 's',
            't': 's'
        }

        for m in gFormatRE.finditer(fmt):
            var = m.group('var')
            pad = m.group('pad')
            fmt_char = format_char_types[var]
            _old = '%s%s' % (pad or '', var)
            _new = '(%s)%s%s' % (var, pad or '', fmt_char)
            fmt = fmt.replace(_old, _new)
        return fmt % self.__attrs__()

    def length(self):
        """:return: The length of the sequence."""
        return len(self)

    def frames(self):
        """:return: List of files in sequence."""
        if not hasattr(self, '__frames') or not self.__frames or self.__NEEDREINDEX:
            self.__frames = list(map(int, self._get_frames()))
            self.__frames.sort()
        return self.__frames

    def start(self):
        """:return: First index number in sequence
        """
        try:
            return self.frames()[0]
        except IndexError:
            return 0

    def end(self):
        """:return: Last index number in sequence
        """
        try:
            return self.frames()[-1]
        except IndexError:
            return 0

    def missing(self):
        """:return: List of missing files."""
        if not hasattr(self, '__missing') or not self.__missing:
            self.__missing = list(map(int, self._get_missing()))
        return self.__missing

    def head(self):
        """:return: String before the sequence index number."""
        return self[0].head

    def tail(self):
        """:return: String after the sequence index number."""
        return self[0].tail

    def path(self):
        """:return: Absolute path to sequence."""
        _dirname = str(os.path.dirname(os.path.abspath(self[0].path)))
        return os.path.join(_dirname, str(self))

    def includes(self, item):
        """Checks if the item can be contained in this sequence that is if it
        is a sibling of any of the items in the list

        For example:

            >>> s = Sequence(['fileA.0001.jpg', 'fileA.0002.jpg'])
            >>> print(s)
            fileA.1-2.jpg
            >>> s.includes('fileA.0003.jpg')
            True
            >>> s.includes('fileB.0003.jpg')
            False
        """
        if len(self) > 0:
            if not isinstance(item, Item):
                item = Item(item)
            if self[-1] != item:
                return self[-1].isSibling(item)
            elif self[0] != item:
                return self[0].isSibling(item)
            else:
                # it should be the only item in the list
                if self[0] == item:
                    return True

        return True

    def contains(self, item):
        """Checks for sequence membership. Calls Item.isSibling() and returns
        True if item is part of the sequence.

        For example:

            >>> s = Sequence(['fileA.0001.jpg', 'fileA.0002.jpg'])
            >>> print(s)
            fileA.1-2.jpg
            >>> s.contains('fileA.0003.jpg')
            False
            >>> s.contains('fileB.0003.jpg')
            False

        :param item: pyseq.Item class object.

        :return: True if item is a sequence member.
        """
        if len(self) > 0:
            if not isinstance(item, Item):
                item = Item(item)
            return self.includes(item)\
                and self.end() >= int(item.frame) >= self.start()

        return False

    def append(self, item):
        """
        Adds another member to the sequence.

        :param item: pyseq.Item object.

        :exc:`SequenceError` raised if item is not a sequence member.
        """
        if type(item) is not Item:
            item = Item(item)

        if self.includes(item):
            super(Sequence, self).append(item)
            self.__frames = None
            self.__missing = None
        else:
            raise SequenceError('Item is not a member of this sequence')

    def get_max_mtime(self):
        '''
        returns the latest mtime of all items
        '''
        maxDate = list()
        for i in self:
            maxDate.append(i.mtime)
        return max(maxDate)
    
    def get_size(self):
        '''
        returns the size all items 
        divide the result by 1024/1024 to get megabytes
        '''
        tempSize = list() 
        for i in self:
            tempSize.append(i.size)
        return sum(tempSize)
    
    def reIndex(self, addSub, padding=None, run=False):
        '''
        renames the files on disk
        reIndex the items in the sequence object egg
        1001 + 100 = 1101
        can change the padding too
        @param addSub int
        @param padding str 
        @param run boolean 
        '''
        if not padding:
            padding = self.format("%p")

        for image,frame in zip(self,self.frames()):
            oldName = image.path
            newFrame = padding % (frame + addSub)
            newFileName ="%s%s%s" % (self.format("%h"), newFrame , self.format("%t") )
            newName = os.path.join(self.dirname, newFileName)
            try:
                import shutil
                if run:
                    shutil.move(oldName,newName)
            except Exception,e:
                log.error(e)
            else:
                log.info('renaming %s -->' % oldName)
                log.info('         %s' % newName)
                self.__NEEDREINDEX = True
                image.frame = newFrame
        else:
            self.frames()

    def _get_padding(self):
        """:return: padding string, e.g. %07d"""
        try:
            pad = len(self._get_frames()[0])
            if pad < 2:
                return '%d'
            return '%%%02dd' % pad
        except IndexError:
            return ''

    def _get_framerange(self, missing=True):
        """
        Returns frame range string, e.g. 1-500.

        :param missing: Expand sequence to exclude missing sequence indices.

        :return: formatted frame range string.
        """
        frange = []
        start = ''
        end = ''

        if not missing:
            if self.frames():
                return '%s-%s' % (self.start(), self.end())
            else:
                return ''

        for i in range(0, len(self.frames())):
            if int(self.frames()[i]) != int(
                    self.frames()[i - 1]) + 1 and i != 0:
                if start != end:
                    frange.append('%s-%s' % (str(start), str(end)))
                elif start == end:
                    frange.append(str(start))
                start = end = self.frames()[i]
                continue
            if start is '' or int(start) > int(self.frames()[i]):
                start = self.frames()[i]
            if end is '' or int(end) < int(self.frames()[i]):
                end = self.frames()[i]
        if start == end:
            frange.append(str(start))
        else:
            frange.append('%s-%s' % (str(start), str(end)))
        return ' '.join(frange)

    def _get_frames(self):
        """finds the sequence indexes from item names
        """
        return [f.frame for f in self if f.frame is not '']

    def _get_missing(self):
        """looks for missing sequence indexes in sequence
        """
        if len(self) > 1:
            frange=None
            try:
                frange = range(self.start(), self.end())
            except:
                frange = range(self.start(), self.end())
            return filter(lambda x: x not in self.frames(), frange)
        return ''


def diff(f1, f2):
    """
    Examines diffs between f1 and f2 and deduces numerical sequence number.

    For example:

        >>> diff('file01_0040.rgb', 'file01_0041.rgb')
        [{'frames': ('0040', '0041'), 'start': 7, 'end': 11}]

        >>> diff('file3.03.rgb', 'file4.03.rgb')
        [{'frames': ('3', '4'), 'start': 4, 'end': 5}]

    :param f1: pyseq.Item object.
    :param f2: pyseq.Item object, for comparison.

    :return: Dictionary with keys: frames, start, end.
    """
    log.debug('diff: %s %s' % (f1, f2))
    if not type(f1) == Item:
        f1 = Item(f1)
    if not type(f2) == Item:
        f2 = Item(f2)

    l1 = [m for m in gDigitsRE.finditer(f1.name)]
    l2 = [m for m in gDigitsRE.finditer(f2.name)]

    d = []
    if len(l1) == len(l2):
        for i in range(0, len(l1)):
            m1 = l1.pop(0)
            m2 = l2.pop(0)
            if m1.start() == m2.start() and m1.group() != m2.group():
                d.append({
                    'start': m1.start(),
                    'end': m1.end(),
                    'frames': (m1.group(), m2.group())
                })

    log.debug(d)
    return d


def uncompress(seq_string, fmt=gFormat):
    """
    Basic uncompression or deserialization of a compressed sequence string.

    For example:

        >>> seq = uncompress('./tests/files/012_vb_110_v001.%04d.png 1-10', fmt='%h%p%t %r')
        >>> print(seq)
        012_vb_110_v001.1-10.png
        >>> len(seq)
        10
        >>> seq2 = uncompress('./tests/files/a.%03d.tga 1-3 10 12-14', fmt='%h%p%t %R')
        >>> print(seq2)
        a.1-14.tga
        >>> len(seq2)
        7
        >>> seq3 = uncompress('a.%03d.tga 1-14 (1-3 10 12-14)', fmt='%h%p%t %r (%R)')
        >>> print(seq3)
        a.1-14.tga
        >>> len(seq3)
        7
        >>> seq4 = uncompress('a.%03d.tga 1-14 (1-3 10 12-14)', fmt='%h%p%t %s-%e (%R)')
        >>> print(seq4)
        a.1-14.tga
        >>> seq5 = uncompress('a.%03d.tga 1-14 (1 14)', fmt='%h%p%t %r (%R)')
        >>> print(seq5)
        a.1-14.tga
        >>> len(seq5)
        2
        >>> seq6 = uncompress('a.%03d.tga 1-14 (1-14)', fmt='%h%p%t %r (%R)')
        >>> print(seq6)
        a.1-14.tga
        >>> len(seq6)
        14
        >>> seq7 = uncompress('a.%03d.tga 1-100000 (1-10 100000)', fmt='%h%p%t %r (%R)')
        >>> print(seq7)
        a.1-100000.tga
        >>> len(seq7)
        11
        >>> seq8 = uncompress('a.%03d.tga 1-100 ([10, 20, 40, 50])', fmt='%h%p%t %r (%m)')
        >>> print(seq8)
        a.1-100.tga
        >>> len(seq8)
        96

    :param seq_string: Compressed sequence string.
    :param fmt: Format of sequence string.

    :return: :class:`.Sequence` instance.
    """
    dirname = os.path.dirname(seq_string)
    name = os.path.basename(seq_string)
    log.debug('uncompress: %s' % name)


    # map of directives to regex
    remap = {
        's': '\d+',
        'e': '\d+',
        'l': '\d+',
        'h': '\S+',
        't': '\S+',
        'r': '\d+-\d+',
        'R': '[\d\s\-]+',
        'p': '%\d+d',
        'm': '\[.*\]',
        'f': '\[.*\]'
    }

    log.debug('fmt in: %s' % fmt)

    # escape any re chars in format
    fmt = re.escape(fmt)
    # replace \% with % back again
    fmt = fmt.replace('\\%', '%')

    log.debug('fmt escaped: %s' % fmt)

    for m in gFormatRE.finditer(fmt):
        _old = '%%%s%s' % (m.group('pad') or '', m.group('var'))
        _new = '(?P<%s>%s)' % (
            m.group('var'),
            remap.get(m.group('var'), '\w+')
        )
        fmt = fmt.replace(_old, _new)

    log.debug('fmt: %s' % fmt)

    regex = re.compile(fmt)
    match = regex.match(name)

    frames = []
    missing = []
    s = None
    e = None

    if not match:
        log.debug('No matches.')
        return

    try:
        pad = match.group('p')
    except IndexError:
        pad = "%d"

    try:
        R = match.group('R')
        log.debug("matched R")
        # 1-10 13 15-20 38
        # expand all the frames
        number_groups = R.split(' ')

        for number_group in number_groups:
            if '-' in number_group:
                splits = number_group.split('-')
                start = int(splits[0])
                end = int(splits[1])
                frames.extend(range(start, end + 1))
            else:
                # just append the number
                end = int(number_group)
                frames.append(end)

    except IndexError:
        try:
            r = match.group('r')
            log.debug('matched r: %s' % r)
            s, e = r.split('-')
            frames = range(int(s), int(e) + 1)
        except IndexError:
            s = match.group('s')
            e = match.group('e')

    try:
        frames = eval(match.group('f'))
    except IndexError:
        pass

    try:
        missing = eval(match.group('m'))
    except IndexError:
        pass

    items = []
    if missing:
        for i in range(int(s), int(e) + 1):
            if i in missing:
                continue
            f = pad % i
            name = '%s%s%s' % (match.group('h'), f, match.group('t'))
            items.append(Item(os.path.join(dirname, name)))
    else:
        for i in frames:
            f = pad % i
            name = '%s%s%s' % (match.group('h'), f, match.group('t'))
            items.append(Item(os.path.join(dirname, name)))

    seqs = getSequences(items)
    if seqs:
        return seqs[0]
    return seqs


def getSequences(source):
    """
    Returns a list of Sequence objects given a directory or list that contain
    sequential members.

    Get sequences in a directory:

        >>> seqs = getSequences('./tests/files/')
        >>> for s in seqs: print(s)
        ...
        012_vb_110_v001.1-10.png
        012_vb_110_v002.1-10.png
        a.1-14.tga
        alpha.txt
        bnc01_TinkSO_tx_0_ty_0.101-105.tif
        bnc01_TinkSO_tx_0_ty_1.101-105.tif
        bnc01_TinkSO_tx_1_ty_0.101-105.tif
        bnc01_TinkSO_tx_1_ty_1.101-105.tif
        file.1-2.tif
        file.info.03.rgb
        file01_40-43.rgb
        file02_44-47.rgb
        file1-4.03.rgb
        file_02.tif
        z1_001_v1.1-4.png
        z1_002_v1.1-4.png
        z1_002_v2.1-4.png

    Get sequences from a list of file names:

        >>> seqs = getSequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
        >>> for s in seqs: print(s)
        ...
        fileA.1-2.rgb
        fileB.1.rgb

    Get sequences from a list of objects, preserving object attrs:

        >>> seqs = getSequences(repo.files())
        >>> seqs[0].date
        datetime.datetime(2011, 3, 21, 17, 31, 24)

    :param source: Can be directory path, list of strings, or sortable list of objects.

    :return: List of pyseq.Sequence class objects.
    """
    start = datetime.now()

    # list for storing sequences to be returned later
    seqs = []

    if isinstance(source, list):
        items = sorted(source, key=lambda x: str(x))
    elif isinstance(source, str):
        if os.path.isdir(source):
            items = sorted(glob(os.path.join(source, '*.*')))
        else:
            items = sorted(glob(source))
    else:
        raise TypeError('Unsupported format for source argument')
    log.debug('Found %s files' % len(items))

    # organize the items into sequences
    while items:
        item = Item(items.pop(0))
        found = False
        for seq in seqs[::-1]:
            if seq.includes(item):
                seq.append(item)
                found = True
                break
        if not found:
            seq = Sequence([item])
            seqs.append(seq)

    log.debug('time: %s' % (datetime.now() - start))
    return list(seqs)
