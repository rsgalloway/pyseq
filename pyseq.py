#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2011-2012, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
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
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ---------------------------------------------------------------------------------------------
# docs and latest version available for download at
#   http://github.com/rsgalloway/pyseq
# ---------------------------------------------------------------------------------------------

__author__ = "Ryan Galloway <ryan@rsgalloway.com>"
__version__ = "0.3.0"

# ---------------------------------------------------------------------------------------------
# TODO
# ---------------------------------------------------------------------------------------------
"""
  - add sequence operations that modify members, e.g. rename, reindex
  - support additional syntax, e.g. x10 for every tenth frame
  - keyboard interrupt (cntl+c)
  - recurse subdirectories and display trees
  - add optional explicit format parameter to diff function
"""

# ---------------------------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------------------------
"""
+v0.3.0 - 2012 Aug 05
  + fixed %R in uncompress()
  + fixed minor bug in getSequences() with glob
  + fixed issue #1: same seqs with different extensions don't compress
  + added some simple inline unit tests

+v0.2.1b - 2011 Mar 23
  + supports sequences of any serializable, sortable items
  + fixes bug in lss

+v0.2.0b - 2011 Mar 14
  + Added support for wildcards in getSequence source input and in lss
  + Added format method to Sequence class for formatted string stdout
  + Sequence __str__ method now returns simplified compressed sequence string
  + Added SequenceError exception
  + Sequence qppend method raises SequenceError if file is non-sequence-member
  + Export diff function to get numeric differences between two sequential files
  + Alpha version of uncompress func for deserialization of compressed sequence strings
  + Added additional attributes to Item class: path, frame, head, tail
  + Item name attribute is now base name, fixes bug where contains method didn't work on file paths
  + Moved function 'main' to lss permanently
  + Added --format and --debug options to lss
  + Ability to set log level with environment variable $PYSEQ_LOG_LEVEL
  + Simplified format directives, e.g. from %(head)s to %h, with support for padding, e.g. %04l
  + Fixed duplicate sequence index number bug
  + Set logging level with PYSEQ_LOG_LEVEL environment variable
  + Added 32 additional test cases
  * Performance improvements
  + Added html docs

+v0.1.2 - 2011 Feb 15
  + getSequences now takes either a directory path or a python list of files
  + added setup.py
  + added lss script
"""

import os
import re
import logging
from glob import glob
from datetime import datetime

# default serialization format string
gFormat = '%04l %h%p%t %R'

# regex for matching numerical characters
gDigitsRE = re.compile(r'\d+')

gStereoRE = re.compile(r'\_left\_|\_right\_|\_l\.|\_r\.')
#testPattern = re.compile(r'\_left\_|\_right\_|\_l\.|\_r\.')
gStereoREFilter = re.compile(r'.*\_left\_.*|.*\_right\_.*|.*\_l\..*|.*\_r\..*')

# regex for matching format directives
gFormatRE = re.compile(r'%(?P<pad>\d+)?(?P<var>\w+)')

__all__ = ['SequenceError', 'FormatError', 'Item', 'Sequence', 'diff', 'uncompress', 
           'getSequences', ]

# logging handlers
log = logging.getLogger('pyseq')

class SequenceError(Exception):
    """special exception for sequence errors"""

class FormatError(Exception):
    """special exception for seq format errors"""

class Item(str):
    """Sequence member file class"""
    def __init__(self, item):
        """
        Create a new Item class object.

        :param item: Path to file.

        :return: pyseq.Item instance.
        """
        super(Item, self).__init__()
        log.debug('adding %s' % item)
        self.item = item
        self.__path = getattr(item, 'path', os.path.abspath(str(item)))
        self.__dirname = os.path.dirname(str(item))
        self.__filename = os.path.basename(str(item))
        self.__digits = gDigitsRE.findall(self.name)
        self.__parts = gDigitsRE.split(self.name)
        self.__size = os.path.getsize(self.__path)
        self.__mtime = os.path.getmtime(self.__path)

        # modified by self.isSibling()
        self.frame = ''
        self.head = self.name
        self.tail = ''

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return '<pyseq.Item "%s">' % self.name

    def __getattr__(self, key):
        return getattr(self.item, key, None)

    def _get_path(self):
        return self.__path

    def _get_filename(self):
        return self.__filename

    def _get_dirname(self):
        return self.__dirname

    def _get_digits(self):
        return self.__digits
    
    def _get_size(self):
        return self.__size
    
    def _get_mtime(self):
        return self.__mtime

    def _get_parts(self):
        return self.__parts

    def _get_sig(self):
        return "".join(self.parts)

    def _set_readonly(self, value):
        raise TypeError, 'Read-only attribute'

    # immutable properties
    path = property(_get_path, _set_readonly, doc="Item absolute path, if a filesystem item.")
    name = property(_get_filename, _set_readonly, doc="Item base name attribute.")
    dirname = property(_get_dirname, _set_readonly, doc="Item directory name, if a filesystem item.")
    digits = property(_get_digits, _set_readonly, doc="Numerical components of item name.")
    size = property(_get_size, _set_readonly, doc="Item Size")
    parts = property(_get_parts, _set_readonly, doc="Non-numerical components of item name.")
    signature = property(_get_sig, _set_readonly, doc="Non-numerical unique item signature.")

    def isSibling(self, item):
        """
        Determines if this and item are part of the same sequence.

        :param item: A pyseq.Item class object.

        :return: True if this and item are sequential siblings.
        """
        if not type(item) == Item:
            item = Item(item)
        d = diff(self, item)
        _isSibling = (len(d) == 1) and (self.parts == item.parts)

        if _isSibling:
            self.frame = d[0]['frames'][0]
            self.head = self.name[:d[0]['start']]
            self.tail = self.name[d[0]['end']:]
            item.frame = d[0]['frames'][1]
            item.head = item.name[:d[0]['start']]
            item.tail = item.name[d[0]['end']:]

        return _isSibling

class Sequence(list):
    """
    Extends list class with methods that handle item sequentialness.

    For example:

        >>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
        >>> print s
        file.1-3.jpg
        >>> s.append('file.0006.jpg')
        >>> print s.format('%04l %h%p%t %R')
           4 file.%04d.jpg 1-3 6
        >>> s.contains('file.0006.jpg')
        True
        >>> s.contains('file.0009.pic')
        False
        >>> print s.format('%h%p%t %r (%R)')
        file.%04d.jpg 1-6 (1-3 6)
    """
    def __init__(self, items):
        """
        Create a new Sequence class object.

        :param: items: Sequential list of items.

        :return: pyseq.Sequence class instance.
        """
        super(Sequence, self).__init__([Item(items.pop(0))])
        self.isStereo = False
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
        return self.format('%h%p%t')

    def __repr__(self):
        return '<pyseq.Sequence "%s">' % str(self)

    def __getattr__(self, key):
        return getattr(self[0], key, None)

    def __contains__(self, item):
        super(Sequence, self).__contains__(Item(item))

    def format(self, format=gFormat):
        """
        Format the stdout string.

        The following directives can be embedded in the format string.
        Format directives support padding, for example: "%%04l".

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

        :param format: Format string. Default is '%04l %h%p%t %R'.

        :return: Formatted string.
        """
        for m in gFormatRE.finditer(format):
            _old = '%s%s' %(m.group('pad') or '', m.group('var'))
            _new = '(%s)%ss' %(m.group('var'), m.group('pad') or '')
            format = format.replace(_old, _new)
        try:
            return format % self.__attrs__()
        except KeyError, e:
            raise 

    def length(self):
        """:return: The length of the sequence."""
        return len(self)

    def frames(self):
        """:return: List of files in sequence."""
        if not hasattr(self, '__frames') or not self.__frames:
            self.__frames = map(int, self._get_frames())
            self.__frames.sort()
        return self.__frames

    def start(self):
        """:return: First index number in sequence."""
        try:
            return self.frames()[0]
        except IndexError:
            if self.length() == 1:
                '''fishy workaround we tend to have the last digit pack as frame numbers'''
                return int(self[0]._get_digits()[-1])
            else:
                return 0

    def end(self):
        """:return: Last index number in sequence."""
        try:
            return self.frames()[-1]
        except IndexError:
            if self.length() == 1:
                '''fishy workaround we tend to have the last digit pack as frame numbers'''
                return int(self[0]._get_digits()[-1])
            else:
                return 0
            
    def missing(self):
        """:return: List of missing files."""
        if not hasattr(self, '__missing') or not self.__missing:
            self.__missing = map(int, self._get_missing())
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
    
    def dirname(self):
        return str(os.path.dirname(os.path.abspath(self[0].path)))

    def contains(self, item):
        """
        Checks for sequence membership. Calls Item.isSibling() and returns
        True if item is part of the sequence.

        For example:

            >>> s = Sequence(['fileA.0001.jpg', 'fileA.0002.jpg'])
            >>> print s
            fileA.1-2.jpg
            >>> s.contains('fileA.0003.jpg')
            True
            >>> s.contains('fileB.0003.jpg')
            False

        :param item: pyseq.Item class object. 

        :return: True if item is a sequence member.
        """
        if len(self) > 0:
            if type(item) is not Item:
                item = Item(item)
            comp = self[-1]
            if comp.isSibling(item) and comp.parts == item.parts:
                return True
        return False

    def append(self, item):
        """
        Adds another member to the sequence.

        :param item: pyseq.Item object. 

        :exc:`SequenceError` raised if item is not a sequence member.
        """
        if type(item) is not Item:
            item = Item(item)
        if self.contains(item):
            super(Sequence, self).append(item)
            self.__frames = None
            self.__missing = None
        else:
            raise SequenceError, 'Item is not a member of this sequence'

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

        :param missing: Expand sequence to exlude missing sequence indices.

        :return: formatted frame range string.
        """
        frange = []
        start = ''
        end = ''
        if not missing:
            if self.frames():
                return '%s-%s' %(self.start(), self.end())
            else:
                return ''
        for i in range(0, len(self.frames())):
            if int(self.frames()[i]) != int(self.frames()[i-1])+1 and i != 0:
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
        """finds the sequence indexes from item names"""
        return [f.frame for f in self if f.frame is not '']

    def _get_missing(self):
        """looks for missing sequence indexes in sequence"""
        if len(self) > 1:
            frange = xrange(self.start(), self.end())
            return filter(lambda x: x not in self.frames(), frange)
        return ''
    
    def _calc_average_size(self, low = None, high= None):
        '''
        returns the average size of items if low and high are indicated
        it calculates the average between those
        '''
        self._sizes = list()
        if not low and not high:
            for i in self:
                self._sizes.append(i._get_size())
        else:
            for i in self[low:high]:
                self._sizes.append(i._get_size())
        self._sizes.remove(min(self._sizes))
        self._sizes.remove(max(self._sizes))
        self._average_size =  (sum(self._sizes)/len(self._sizes))
        return self._average_size
    
    def _get_fishy_sizes(self,threshold = 5):
        '''
        returns items which differ from the average in percent 
        '''
        self._calc_average_size()
        percent = self._average_size * (threshold/100.0) 
        minV = self._average_size - percent
        maxV = self._average_size + percent
        self._fishy_files = list()
        for i in self:
            if i._get_size() < minV or i._get_size() > maxV:
                 self._fishy_files.append(i)
                 
        return self._fishy_files
    
    def _get_size_jumps(self, threshold = 5, frameRange = 10):
        '''
        returns a list of dicts 
        per item a dict is created with the item under the key item and the average filesize
        '''
        
        self._fishy_jump = list()
        
        for e, i in enumerate(self):
            tempDict = dict()
            if e <= frameRange/2.0:
                high = e + frameRange/2
                low = 0
            elif frameRange/2.0 < e < len(self)-frameRange/2.0:
                high = e + frameRange/2
                low = e - frameRange/2
            elif e >= len(self)-frameRange/2.0:
                high = len(self)-1
                low = e - frameRange/2
            tempAvg = self._calc_average_size(low=low,high=high)
            percent = tempAvg * (threshold/100.0) 
            minV = tempAvg - percent
            maxV = tempAvg + percent
            if i._get_size() < minV or i._get_size() > maxV:
                 tempDict['item'] = i
                 tempDict['avgSize'] = tempAvg
                 self._fishy_jump.append(tempDict)
            
        if self._fishy_jump:
            log.info('found %s items %s that vary in size by %s percent in an average range of %s frames' % (len(self._fishy_jump),self._fishy_jump,threshold,frameRange))
        return self._fishy_jump
    
    def _create_mov(self, resX = 1724, resY = 936, soundFile = None, **kwargs):
        '''
        little wrapper to create an mov from a sequence object
        '''
        oldExt = self.format("%t").split('.')[-1]
        newDirname = self.dirname().replace(oldExt, 'mov')
        mjpgName = os.path.join(newDirname, self.format("%h.mov"))
        mjpgName =mjpgName.replace('..','.')
        from helper import srConverter
        convert = srConverter.srConverter()
        convert.generateMjpgAFromImageSequence(self.path(),self.start(), self.end(),mjpgName, resX = resX, resY = resY, soundFile = soundFile, **kwargs)
        return mjpgName
    
    def _create_mp4(self,resX = 1724, resY = 936, soundFile = None, **kwargs):
        '''
        little wrapper to create an mov from a sequence object
        '''
        oldExt = self.format("%t").split('.')[-1]
        newDirname = self.dirname().replace(oldExt, 'mp4')
        mp4Name = os.path.join(newDirname, self.format("%h.mp4"))
        mp4Name =mp4Name.replace('..','.')
        from helper import srConverter
        convert = srConverter.srConverter()
        convert.generateMp4FromImageSequence(self.path(),self.start(), self.end(),mp4Name, resX = resX, resY = resY, soundFile = soundFile, **kwargs)
        return mp4Name
    
    def _get_max_mtime(self):
        '''
        returns the latest mtime of all items
        '''
        maxDate = list()
        for i in self:
            maxDate.append(i._get_mtime())
        log.info('returning max time from mono object')
        return max(maxDate)
        
    def _get_size(self):
        '''
        returns the size all items 
        divide the result by 1024/1024 to get megabytes
        '''
        tempSize = list() 
        for i in self:
            tempSize.append(i._get_size())
        return sum(tempSize)
    
class stereoSequence(Sequence):


    def __init__(self, items, left, right):
        
        super(Sequence, self).__init__([Item(items.pop(0))])
        self.isStereo = False
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
        
        self.left = left
        self.right = right
        self.isStereo = True

    def __str__(self):
        lPattern = re.compile(r'\_l\.|\_r\.')
        leftPattern = re.compile(r'\_left\_|\_right\_')
        lFilter = re.compile(r'.*\_l\..*|.*\_r\..*')
        leftFilter = re.compile(r'.*\_left\_.*|.*\_right\_.*')
        if re.match(lFilter,self.left.format('%h%p%t')):
            return re.sub(lPattern,'_%v.',self.left.format('%h%p%t'))
        elif re.match(leftFilter,self.left.format('%h%p%t')):
            return re.sub(leftPattern,'_%V_',self.left.format('%h%p%t'))

    def _get_max_mtime(self):
        '''
        returns the latest mtime of all items left and right
        '''
        maxDate = list()
        for i in self.left:
            maxDate.append(i._get_mtime())
        for i in self.right:
            maxDate.append(i._get_mtime())
        log.info('returning max time from s3d object')
        return max(maxDate)
    
    def _get_size(self):
        '''
        returns the size all items left and right in bytes
        divide the result by 1024/1024 to get megabytes
        '''
        tempSize = list() 
        for i in self.left:
            tempSize.append(i._get_size())
        for i in self.right:
            tempSize.append(i._get_size())
        return sum(tempSize)

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
    log.debug('diff: %s %s' %(f1, f2))
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
                d.append({'start': m1.start(), 
                          'end': m1.end(), 
                          'frames': (m1.group(), m2.group())}
                )

    log.debug(d)
    return d

def uncompress(seqstring, format=gFormat):
    """
    Basic uncompression or deserialization of a compressed sequence string.

    For example: 

        >>> seq = uncompress('./tests/012_vb_110_v001.%04d.png 1-10', format='%h%p%t %r')
        >>> print seq
        012_vb_110_v001.1-10.png
        >>> len(seq)
        10
        >>> seq2 = uncompress('./tests/a.%03d.tga 1-3 10 12-14', format='%h%p%t %R')
        >>> print seq2
        a.1-14.tga
        >>> len(seq2)
        7
        >>> seq3 = uncompress('a.%03d.tga 1-14 (1-3 10 12-14)', format='%h%p%t %r (%R)')
        >>> print seq3
        a.1-14.tga
        >>> len(seq3)
        7
        >>> seq4 = uncompress('a.%03d.tga 1-14 (1-3 10 12-14)', format='%h%p%t %s-%e (%R)')
        >>> print seq4
        a.1-14.tga
        >>> len(seq3)
        7
        >>> seq5 = uncompress('a.%03d.tga 1-14 (1 14)', format='%h%p%t %r (%R)')
        >>> print seq5
        a.1-14.tga
        >>> len(seq5)
        2
        >>> seq6 = uncompress('a.%03d.tga 1-14 (1-14)', format='%h%p%t %r (%R)')
        >>> print seq6
        a.1-14.tga
        >>> len(seq6)
        14
        >>> seq7 = uncompress('a.%03d.tga 1-100000 (1-10 100000)', format='%h%p%t %r (%R)')
        >>> print seq7
        a.1-100000.tga
        >>> len(seq7)
        11
        >>> seq8 = uncompress('a.%03d.tga 1-100 ([10, 20, 40, 50])', format='%h%p%t %r (%m)')
        >>> print seq8
        a.1-100.tga
        >>> len(seq8)
        96

    :param seqstring: Compressed sequence string. 
    :param format: Format of sequence string.

    :return: pyseq.Sequence instance.
    """
    dirname = os.path.dirname(seqstring)
    name = os.path.basename(seqstring)
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

    log.debug('format in: %s' % format)

    # escape any re chars in format
    format = re.escape(format)

    # replace \% with % back again
    format = format.replace('\\%', '%')

    log.debug('format escaped: %s' % format)

    for m in gFormatRE.finditer(format):
        _old = '%%%s%s' % (m.group('pad') or '', m.group('var'))
        _new = '(?P<%s>%s)' % (m.group('var'), remap.get(m.group('var'), '\w+'))
        format = format.replace(_old, _new)

    log.debug('format: %s' % format)

    regex = re.compile(format)
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
                frames.extend(range(start, end+1))
            else:
                # just append the number
                end = int(number_group)
                frames.append(end)

    except IndexError:
        try:
            r = match.group('r')
            log.debug('matched r: %s' % r)
            s, e = r.split('-')
            frames = range(int(s), int(e)+1)
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
        for i in range(int(s), int(e)+1):
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

def getSequences(source,stereo=False,folders=True):
    """
    Returns a list of Sequence objects given a directory or list that contain
    sequential members.

    Get sequences in a directory:

        >>> seqs = getSequences('./tests/')
        >>> for s in seqs: print s
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
        >>> for s in seqs: print s
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

    # list for storing sequences to be returnd later
    seqs = []

    # glob the source items and sort them
    if type(source) == list:
        items = sorted(source, key=lambda x: str(x))
    elif type(source) == str and os.path.isdir(source) and folders:
        items = sorted(glob(os.path.join(source, '*')))
    elif type(source) == str and os.path.isdir(source) and not folders:
        items = sorted(glob(os.path.join(source, '*.*')))
    elif type(source) == str:
        items = sorted(glob(source))
    else:
        raise TypeError, 'Unsupported format for source argument'
    log.debug('Found %s files' % len(items))

    # organize the items into sequences
    while items:
        item = Item(items.pop(0))
        found = False
        for seq in seqs[::-1]:
            if seq.contains(item):
                seq.append(item)
                found = True
                break
        if not found:
            seq = Sequence([item])
            seqs.append(seq)

    log.debug("time: %s" %(datetime.now() - start))
    if not stereo:
        log.info("added sequences: %s" %(seqs))
        return seqs
    else:

        listName = []
        left = []
        right = []
        newSeqs = []
        seqs.sort()
        
        ### this is super unsexy but a fair assumption but it needs to be extended...
        ### checking for pairs somehow or rewrite the entire s3d thingy
        if len(seqs) == 1:
            newSeqs = seqs
        else:
            for i in seqs:
                if re.match(gStereoREFilter,str(i)):
                    log.info("stereo detected for %s" % i)
                    listName.append((gStereoRE.finditer(str(i)),i))
                else:
                    newSeqs.append(i)
                    
        for d in listName:
            for x in d[0]:
                eye = re.sub(r'[^A-Za-z]','', x.group())
                log.debug('found eye %s' % eye)
                if eye == 'left' or eye == 'l' :
                    left.append({'index':x.span(),'file':d[1],'start':d[1].format('%h%p%t')[:x.start()],'end':d[1].format('%h%p%t')[x.end():]})
                elif eye == 'right' or eye == 'r' :
                    right.append({'index':x.span(),'file':d[1],'start':d[1].format('%h%p%t')[:x.start()],'end':d[1].format('%h%p%t')[x.end():]})

        
        for l,r in zip(left,right):
            ## assuming that the order dictates that the stereo pairs reside at the same index..
            if l['start'] == r['start'] and l['end'] == r['end']:
                newSeqs.append(stereoSequence(l['file'][:],l['file'],r['file']))
        
        log.debug("time: %s" %(datetime.now() - start))
        log.info("added sequences: %s" %(newSeqs))
        return newSeqs

def img2pyseq(path,stereo=True):
    '''
    path string can be either an evaluated path 
    like prj_SQ0010_SH0010_matte_base_v001_l.1001.exr
    or prj_SQ0010_SH0010_matte_base_v001_%v.%04d.exr
    '''
    stereoRe = re.compile(r'\_left\.|\_right\.|\_l\.|\_r\.|\_\%v\.')
    padding = re.compile(r'[0-9]{4}\.|\%04d\.|\%d\.|\%02d\.|\%03d\.|\%05d\.|\#\.|\#\#\.|\#\#\#\.|\#\#\#\#\.|[0-9]*\-[0-9]*\#\.')
    path = re.sub(padding, '*.' , path)
    path = re.sub(stereoRe, '_*.',path)
    seq = getSequences(path,stereo=stereo,folders=False)
    if not seq:
        return None
    else:
        for i in seq:
            if not str(i).__contains__('_c.'):
                return i




if __name__ == '__main__':
    """
    Run some simple unit tests. Currently, these tests depend on the
    dummy files that live in pyseq/tests. Changing or modifying these
    files may break the assertions in the tests below.
    """

    # test passing in a list of files
    seqs = getSequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
    assert len(seqs) == 2

    # get a diff of two files in the same seq
    d = diff('fileA.0001.dpx', 'fileA.0002.dpx')
    assert d[0]['frames'] == ('0001', '0002')

    # get a diff of two files in the same seq
    d = diff('012_vb_110_v002.1.dpx', '012_vb_110_v002.2.dpx')
    assert d[0]['frames'] == ('1', '2')

    # glob some files from the tests dir
    seqs = getSequences('tests/fileA.*')
    assert len(seqs) == 2

    # uncompress a few files, test the format matching
    seq = uncompress('./tests/012_vb_110_v001.%04d.png 1-10', format='%h%p%t %r')
    assert len(seq) == 10
    assert seq.head() == '012_vb_110_v001.' and seq.tail() == '.png'
    assert seq.frames() == range(1, 11)

    # ... with slightly different format matching
    seq = uncompress('./tests/012_vb_110_v001.1-10.png', format='%h%r%t')
    assert len(seq) == 10
    assert seq.head() == '012_vb_110_v001.' and seq.tail() == '.png'
    assert seq.frames() == range(1, 11)

    # grab all the seqs in the tests dir
    seqs = getSequences(os.path.join(os.path.dirname(__file__), 'tests'))
    for s in seqs:
        print s.format('%h%p%t %r')

