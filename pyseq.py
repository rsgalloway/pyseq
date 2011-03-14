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
__version__ = "0.2.0b"

# ---------------------------------------------------------------------------------------------
# TODO
# ---------------------------------------------------------------------------------------------
"""
  - support additional syntax, e.g. x10 = every tenth frame
  - recurse subdirectories and display trees
  - add optional format parameter to diff function
"""

# ---------------------------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------------------------
"""
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
import sys
import difflib
import logging
from glob import glob
from datetime import datetime

# default serialization format string
gFormat = '%04l %h%p%t %R'

# regex for matching numerical characters
gDigitsRE = re.compile(r'\d+')

# regex for matching format directives
gFormatRE = re.compile(r'%(?P<pad>\d+)?(?P<var>\w+)')

__all__ = ['SequenceError', 'Item', 'Sequence', 'diff', 'uncompress', 'getSequences']

log = logging.getLogger('pyseq')
log.addHandler(logging.StreamHandler())
log.setLevel(int(os.environ.get('PYSEQ_LOG_LEVEL', logging.INFO)))

# -----------------------------------------------------------------------------
class SequenceError(Exception):
    """special exception for sequence errors"""
    
class Item(str):
    """Sequence member file class"""
    def __init__(self, path):
        """
        Create a new Item class object.
        
        :param path: Path to file.
        
        :return: pyseq.Item instance.
        """
        self.__path = os.path.abspath(path)
        self.__dirname = os.path.dirname(path)
        self.__filename = os.path.basename(self.path)
        self.__digits = gDigitsRE.findall(self.name)
        self.__parts = gDigitsRE.split(self.name)
        
        # modified by self.isSibling()
        self.frame = ''
        self.head = self.name
        self.tail = ''
        
    def __str__(self):
        return str(self.name)
    
    def __repr__(self):
        return '<pyseq.Item "%s">' % self.name
        
    def _get_path(self):
        return self.__path
   
    def _get_filename(self):
        return self.__filename
        
    def _get_dirname(self):
        return self.__dirname
    
    def _get_digits(self):
        return self.__digits
    
    def _get_parts(self):
        return self.__parts
        
    def _set_readonly(self, value):
        raise TypeError, 'Read-only attribute'
    
    # immutable properties
    path = property(_get_path, _set_readonly, doc="Item absolute path, if a filesystem item.")
    name = property(_get_filename, _set_readonly, doc="Item base name attribute.")
    dirname = property(_get_dirname, _set_readonly, doc="Item directory name, if a filesystem item.")
    digits = property(_get_digits, _set_readonly, doc="Numerical components of item name.")
    parts = property(_get_parts, _set_readonly, doc="Non-numerical components of item name.")
            
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
        >>> s.contains('file.0009.jpg')
        True
        >>> s.contains('file.0009.pic')
        False
    """
    def __init__(self, items):
        """
        Create a new Sequence class object.
        
        :param: items: Sequential list of items.
        
        :return: pyseq.Sequence class instance.
        """
        super(Sequence, self).__init__([Item(items.pop(0))])
        while items:
            f = Item(items.pop(0))
            try:
                self.append(f)
                log.debug('+Item belongs to sequence.')
            except SequenceError, e:
                continue
                log.debug('-Item does not belong to sequence.')
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
        return format % self.__attrs__()
        
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
            return 0
            
    def end(self):
        """:return: Last index number in sequence."""
        try:
            return self.frames()[-1]
        except IndexError:
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
            return self[-1].isSibling(item)
        
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
        prev = ''
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

    :param seqstring: Compressed sequence string. 
    :param format: Format of sequence string.
    
    :return: pyseq.Sequence instance.
    """
    dirname = os.path.dirname(seqstring)
    name = os.path.basename(seqstring)
    log.debug('uncompress: %s' % name)
    
    #FIXME: RE for directive 'R' is broken
    remap = {
        's': '\d+',
        'e': '\d+',
        'l': '\d+',
        'h': '\S+',
        't': '\S+',
        'r': '\d+-\d+',
        'R': '\d+',
        'p': '%\d+d',
        'm': '\[.*\]',
        'f': '\[.*\]'
    }
    
    for m in gFormatRE.finditer(format):
        _old = '%%%s%s' %(m.group('pad') or '', m.group('var'))
        _new = '(?P<%s>%s)' %(m.group('var'), remap.get(m.group('var'), '\w+'))
        format = format.replace(_old, _new)
    
    regex = re.compile(format)
    match = regex.match(name)
    
    if not match:
        log.debug('No matches.')
        return
        
    try:
        pad = match.group('p')
    except IndexError:
        pad = "%d"
    
    try:
        r = match.group('r')
        s, e = r.split('-')
    except IndexError:
        s = match.group('s')
        e = match.group('e')
        
    try:
        frames = eval(m.group('f'))
    except IndexError:
        frames = []
        
    try:
        missing = eval(m.group('m'))
    except IndexError:
        missing = []
    
    items = []
    for i in range(int(s), int(e)+1):
        if i in missing:
            continue
        exec('f = "%s" %% i' % pad)
        name = '%s%s%s' %(match.group('h'), f, match.group('t'))
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
    
        >>> seqs = getSequences('./tests/')
        >>> for s in seqs: print s
        ... 
        012_vb_110_v001.1-10.png
        012_vb_110_v002.1-10.png
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
        
    Get sequences from a list:
        
        >>> seqs = getSequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
        >>> for s in seqs: print s
        ... 
        fileA.1-2.rgb
        fileB.1.rgb
       
    :param source: Can be directory path or list of items.  
      
    :return: List of pyseq.Sequence class objects.
    """
    seqs = []
    s = datetime.now()
    
    if type(source) == list:
        items = source
        items.sort()
    elif type(source) == str and os.path.isdir(source):
        items = glob(os.path.join(source, '*'))
    elif type(source) == str:
        items = glob(source)
    else:
        raise TypeError, 'Unsupported format for source argument'
        
    log.debug('Found %s files' % len(items))
    if len(items) > 0:
        seq = Sequence([Item(items.pop(0))])
        seqs.append(seq)
        while items:
            item = Item(items.pop(0))
            try:
                seq.append(item)
                log.debug('+Item belongs to sequence.')
            except SequenceError, e:
                seq = Sequence([item])
                seqs.append(seq)
                log.debug('-Item does not belong to sequence.')
            except KeyboardInterrupt:
                log.info("Stopping.")
                break
                
        log.debug('Done in %s.' %(datetime.now() - s))
    return seqs
    
if __name__ == '__main__':
    """run through some test examples"""
    seqs = getSequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
    print seqs
    seqs = getSequences(os.path.join(os.path.dirname(__file__), 'tests'))
    for s in seqs: print s.format('%h%p%t %r')
    print diff('fileA.0001.dpx', 'fileA.0002.dpx')
    print diff('012_vb_110_v002.1.dpx', '012_vb_110_v002.2.dpx')
    seq = uncompress('./tests/012_vb_110_v001.%04d.png 1-10', format='%h%p%t %r')
    print seq.format()
    seq = uncompress('./tests/012_vb_110_v001.1-10.png', format='%h%r%t')
    print seq.format()