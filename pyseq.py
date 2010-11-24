#!/usr/bin/env python
"""
pyseq

Copyright 2010 Ryan Galloway (http://www.rsgalloway.com)

Find sequences of files that can be compressed together.

Sequences are defined as groups of files following a naming convention with:
    - one or less integer match differences belong to the same sequence,
    - two or more integer match differences belong to different sequences.

For example:

> ls
alpha.txt        file01_0043.rgb  file02_0047.rgb  file4.03.rgb
file01_0040.rgb  file02_0044.rgb  file1.03.rgb     file.info.03.rgb
file01_0041.rgb  file02_0045.rgb  file2.03.rgb
file01_0042.rgb  file02_0046.rgb  file3.03.rgb

> lss
   1 alpha.txt
   1 file.info.03.rgb
   4 file01_%04d.rgb    40-43
   4 file02_%04d.rgb    44-47
   4 file%d.03.rgb      1-4

However, you could also argue that this one:

   4 file%d.03.rgb              1-4
 
is actually frame 3 of four unique sequences, which I think is probably a more
common use case. So, it's important to establish naming conventions early on,
for example PTS #s could potentially be mistaken for frame numbers.

"""
__author__ = "Ryan Galloway <ryan@rsgalloway.com>"
__version__ = "0.1.0"
__license__ = "Creative Commons 3.0 BY-SA "
__docformat__ = 'restructuredtext'

import sys
import re
import os

gFormat = '%(length)04s %(preseq)s%(padding)s%(postseq)s%(spacing)s%(framerange)s'
gRegex = re.compile(r'\d+')

__all__ = ['File', 'Sequence', 'getSequences']

# -----------------------------------------------------------------------------
class File(object):
    """sequence member file class"""
    def __init__(self, name):
        self.__filename = name
        self.__digits = gRegex.findall(self.name)
        self.__parts = gRegex.split(self.name)
        
    def __str__(self):
        return str(self.name)
    
    def __repr__(self):
        return repr(self.name)
   
    def _get_filename(self):
        return self.__filename
    
    def _get_digits(self):
        return self.__digits
    
    def _get_parts(self):
        return self.__parts
        
    def _set_readonly(self, value):
        raise TypeError, 'readonly attribute'
        
    name = property(_get_filename, _set_readonly)
    digits = property(_get_digits, _set_readonly)
    parts = property(_get_parts, _set_readonly)
    
    def compare(self, fileObject):
        """returns a list of file name differences"""
        assert type(fileObject) == File, 'expecting File type, found %s' % type(fileObject)
        l1 = self.parts + self.digits
        l2 = fileObject.parts + fileObject.digits
        sd = set(l1).difference(set(l2))
        return list(sd)
            
    def isSibling(self, fileObject):
        """returns True if this file and fileObject are sequential siblings"""
        assert type(fileObject) == File, 'expecting File type, found %s' % type(fileObject)
        diffs = self.compare(fileObject)
        return (diffs is not None and len(diffs) == 1 and diffs[0] in self.digits)

class Sequence(list):
    """
    extends list class with methods that handle sequentialness, for example:
    
    >>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
    >>> s
    ['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg']
    >>> print s
       3 file.%04d.jpg      1-3
    >>> s.append('file.0006.jpg')
    >>> print s
       4 file.%04d.jpg      1-3 6
    >>> s.contains('file.0009.jpg')
    True
    >>> s.contains('file.0009.pic')
    False
    """
    def __init__(self, filenames):
        super(Sequence, self).__init__(map(File, filenames))
        
    def __str__(self):
        self.length = len(self)
        self.frames = map(int, self._get_frames())
        self.missing = map(int, self._get_missing())
        self.padding = self._get_padding()
        self.framerange = self._get_framerange()
        self.preseq = self._get_preseq()
        self.postseq = self._get_postseq()
        self.spacing = '\t'* (1 + (1 * (12 > len(self[0].name))))
        return gFormat % self.__dict__
    
    def append(self, filename):
        super(Sequence, self).append(File(filename))
        
    def contains(self, fileObject):
        """checks for sequence membership (but not list membership)"""
        if len(self) > 0:
            if type(fileObject) is not File:
                fileObject = File(fileObject)
            return self[0].isSibling(fileObject)
        
    def _get_padding(self):
        if len(self) > 1:
            pad = len(self._get_frames()[0])
            if pad < 2:
                return '%d'
            return '%%%02dd' % pad
        return ''
    
    def _get_framerange(self):
        frange = []
        start = ''
        end = ''
        prev = ''
        for i in range(len(self.frames)):
            if int(self.frames[i]) != int(self.frames[i-1])+1 and i != 0:
                if start != end:
                    frange.append('%s-%s' % (str(start), str(end)))
                elif start == end:
                    frange.append(str(start))
                start = end = self.frames[i]
                continue
            if start is '' or int(start) > int(self.frames[i]):
                start = self.frames[i]
            if end is '' or int(end) < int(self.frames[i]):
                end = self.frames[i]
        if start == end:
            frange.append(str(start))
        else:
            frange.append('%s-%s' % (str(start), str(end)))
        return ' '.join(frange)
    
    def _get_preseq(self):
        if len(self) > 1:
            return str(self[0]).split(self._get_frames()[0])[0]
        return self[0].name
    
    def _get_postseq(self):
        if len(self) > 1:
            return str(self[0]).split(self._get_frames()[0])[-1]
        return ''
    
    def _get_frames(self):
        frames = []
        if len(self) > 1:
            digitSet = set(self[0].digits)
            for next in self:
                frames.extend(list(digitSet.symmetric_difference(next.digits)))
            frames = list(set(frames))
            frames.sort()
        return frames
    
    def _get_missing(self):
        if len(self) > 1:
            frange = xrange(self.frames[0], self.frames[-1])
            return filter(lambda x: x not in self.frames, frange)
        return ''
        
def getSequences(directory):
    """
    returns a list of Sequence objects given a directory that contain sequential 
    members, for example:
    
    seqs = getSequences('/directory/path/')
    for s in seqs: print s
    ...
       1 alpha.txt
       7 bm3k.%04d.jpg      1-3 5-6 9-10
       1 file.info.03.rgb
       4 file01_%04d.rgb    40-43
       4 file02_%04d.rgb    44-47
       4 file%d.03.rgb      1-4
    """
    seqs = []
    if os.path.isdir(directory):
        seqs = []
        files = os.listdir(directory)
        files.sort()
        for filename in files:
            if len(seqs) == 0:
                seqs.append(Sequence([filename]))
            else:
                newSequence = True
                for seq in seqs:
                    if seq.contains(filename):
                        seq.append(filename)
                        newSequence = False
                        break
                if newSequence:
                    seqs.append(Sequence([filename]))
    return seqs
    
# -----------------------------------------------------------------------------
def main():
    import optparse
    parser = optparse.OptionParser(usage="lss [path]", version="%prog 0.1.0")
    (options, args) = parser.parse_args()

    path = os.path.curdir
    if len(args) > 0:
        path = args[0]
    print '\n'.join([str(seq) for seq in getSequences(path)])
    return (0)

if __name__ == '__main__':
    sys.exit(main())
    
