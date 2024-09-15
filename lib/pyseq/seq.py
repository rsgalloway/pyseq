#!/usr/bin/env python
#
# Copyright (c) 2011-2024, Ryan Galloway (ryan@rsgalloway.com)
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

__doc__ = """
Contains the main pyseq classes and functions.
"""

import functools
import os
import re
import traceback
import warnings
from collections import deque
from glob import glob, iglob

from pyseq.util import _ext_key

# default serialization format string
global_format = "%4l %h%p%t %R"
default_format = "%h%r%t"

# use strict padding on sequences (pad length must match)
#    $ export PYSEQ_STRICT_PAD=1 or
#    $ export PYSEQ_NOT_STRICT=1
# to enable/disable. disabled by default.
strict_pad = (
    int(os.getenv("PYSEQ_STRICT_PAD", 0)) == 1
    or int(os.getenv("PYSEQ_NOT_STRICT", 1)) == 0
)

# regex for matching numerical characters
digits_re = re.compile(r"\d+")

# regex for matching format directives
format_re = re.compile(r"%(?P<pad>\d+)?(?P<var>\w+)")

# character to join explicit frame ranges on
range_join = os.environ.get("PYSEQ_RANGE_SEP", ", ")


class SequenceError(Exception):
    """Special exception for Sequence errors."""

    pass


class FormatError(Exception):
    """Special exception for Sequence format errors."""

    pass


def padsize(item, frame):
    """
    Determines the pad size for a given Item. Return value may depend on
    whether strict padding is enabled or not.

    For example: the file item.001.exr will have a pad size of 3, and the
    file test.001001.exr will have a pad size of 6.

    :param item: Item object.
    :param frame: the frame number as a string.
    :returns: the size of the frame pad as an int.
    """

    # strict: frame size (%d) must match between frames (default)
    # for example: test.09.jpg, test.10.jpg, test.11.jpg
    if strict_pad:
        return item.pad or len(frame)

    # not strict: frame size can change between frames
    # for example: test.9.jpg, test.10.jpg, test.11.jpg
    else:
        return item.pad or len(frame) if frame.startswith("0") else 0


class Item(str):
    """
    Represents a file in a sequence.
    """

    def __init__(self, item):
        """
        Initializes a new instance of the Item class.

        :param item: Path to the file.
        """
        super(Item, self).__init__()
        self.item = item
        self.__path = getattr(item, "path", None)
        if self.__path is None:
            self.__path = str(item)
        self.__filename = os.path.basename(self.__path)
        self.__number_matches = []
        self.__parts = digits_re.split(self.name)
        self.__stat = None

        # modified by self.is_sibling()
        self.frame = None
        self.head = self.name
        self.tail = ""
        self.pad = None

    def __eq__(self, other):
        """
        Checks if this Item is equal to another Item.

        :param other: Another Item instance.
        :return: True if the Items are equal, False otherwise.
        """
        return self.path == other.path

    def __ne__(self, other):
        """
        Checks if this Item is not equal to another Item.

        :param other: Another Item instance.
        :return: True if the Items are not equal, False otherwise.
        """
        return self.path != other.path

    def __lt__(self, other):
        """
        Checks if this Item is less than another Item.

        :param other: Another Item instance.
        :return: True if this Item is less than the other Item, False otherwise.
        """
        return self.frame < other.frame

    def __gt__(self, other):
        """
        Checks if this Item is greater than another Item.

        :param other: Another Item instance.
        :return: True if this Item is greater than the other Item, False otherwise.
        """
        return self.frame > other.frame

    def __ge__(self, other):
        """
        Checks if this Item is greater than or equal to another Item.

        :param other: Another Item instance.
        :return: True if this Item is greater than or equal to the other Item, False otherwise.
        """
        return self.frame >= other.frame

    def __le__(self, other):
        """
        Checks if this Item is less than or equal to another Item.

        :param other: Another Item instance.
        :return: True if this Item is less than or equal to the other Item, False otherwise.
        """
        return self.frame <= other.frame

    def __hash__(self):
        """
        Returns the hash value of this Item.

        :return: The hash value.
        """
        return hash(self.path)

    def __str__(self):
        """
        Returns the string representation of this Item.

        :return: The string representation.
        """
        return str(self.name)

    def __repr__(self):
        """
        Returns the official string representation of this Item.

        :return: The official string representation.
        """
        return '<pyseq.Item "%s">' % self.name

    def __getattr__(self, key):
        """
        Retrieves the value of the specified attribute.

        :param key: The name of the attribute.
        :return: The value of the attribute.
        """
        return getattr(self.item, key)

    @property
    def path(self):
        """
        Gets the absolute path of the Item, if it is a filesystem item.

        :return: The absolute path.
        """
        return self.__path

    @property
    def name(self):
        """
        Gets the base name of the Item.

        :return: The base name.
        """
        return self.__filename

    @property
    def dirname(self):
        """
        Gets the directory name of the Item, if it is a filesystem item.

        :return: The directory name.
        """
        return os.path.dirname(self.__path)

    @property
    def digits(self):
        """
        Returns the numerical components of the Item as a list of strings.

        :return: The numerical components.
        """
        return digits_re.findall(self.__filename)

    @property
    def number_matches(self):
        """
        Returns the numerical components of the Item as a list of regex match objects.

        :return: The numerical components.
        """
        if not self.__number_matches:
            self.__number_matches = list(digits_re.finditer(self.__filename))
        return self.__number_matches

    @property
    def parts(self):
        """
        Returns the non-numerical components of the Item.

        :return: The non-numerical components.
        """
        return self.__parts

    @property
    def exists(self):
        """
        Checks if this Item exists on disk.

        :return: True if the Item exists, False otherwise.
        """
        return os.path.isfile(self.__path)

    @property
    def size(self):
        """
        Returns the size of the Item, reported by os.stat.

        :return: The size of the Item.
        """
        return self.stat.st_size

    @property
    def mtime(self):
        """
        Returns the modification time of the Item.

        :return: The modification time.
        """
        return self.stat.st_mtime

    @property
    @functools.lru_cache(maxsize=None)
    def stat(self):
        """
        Returns the os.stat object for this file.

        :return: The os.stat object.
        """
        if self.__stat is None:
            self.__stat = os.stat(self.__path)
        return self.__stat

    def is_sibling(self, item):
        """
        Determines if this Item and another Item are part of the same sequence.

        :param item: Another Item instance.

        :return: True if this Item and the other Item are sequential siblings, False otherwise.
        """
        if not isinstance(item, Item):
            item = Item(item)

        # diff these two items to determine siblinghood
        d = diff(self, item)
        is_sibling = (len(d) == 1) and (self.parts == item.parts)

        # if these items are in the same sequence, set some common attributes on both items
        if is_sibling:
            frame = d[0]["frames"][0]
            self.frame = int(frame)
            self.pad = padsize(item, frame)
            self.head = self.name[: d[0]["start"]]
            self.tail = self.name[d[0]["end"] :]  # noqa
            frame = d[0]["frames"][1]
            item.frame = int(frame)
            item.pad = self.pad
            item.head = item.name[: d[0]["start"]]
            item.tail = item.name[d[0]["end"] :]  # noqa

        return is_sibling


class Sequence(list):
    """Extends list class with methods that handle item sequentialness.

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
        # otherwise Sequence consumes the list
        items = deque(items[::])
        super(Sequence, self).__init__([Item(items.popleft())])
        self.__missing = []
        self.__dirty = False
        self.__frames = None

        while items:
            f = Item(items.popleft())
            try:
                self.append(f)
            except SequenceError:
                continue
            except KeyboardInterrupt:
                print("Stopping.")
                break

    def __attrs__(self):
        """Replaces format directives with callables to get their values."""
        return {
            "l": self.length,
            "s": self.start,
            "e": self.end,
            "f": self.frames,
            "m": self.missing,
            "M": functools.partial(self._get_framerange, self.missing(), missing=True),
            "d": lambda *x: self.size,
            "H": lambda *x: self.human,
            "D": self.directory,
            "p": self._get_padding,
            "r": functools.partial(self._get_framerange, self.frames(), missing=False),
            "R": functools.partial(self._get_framerange, self.frames(), missing=True),
            "h": self.head,
            "t": self.tail,
        }

    def __str__(self):
        return self.format(default_format)

    def __repr__(self):
        return '<pyseq.Sequence "%s">' % str(self)

    def __getattr__(self, key):
        return getattr(self[0], key)

    def __contains__(self, item):
        super(Sequence, self).__contains__(Item(item))

    def __setitem__(self, index, item):
        """Used to set a particular element in the sequence"""
        if type(index) is slice:
            if index.step not in (1, None):
                raise ValueError("only step=1 supported")
            if isinstance(item, str):
                item = Sequence([item])
            super(Sequence, self).__setitem__(index, item)
            return
        if not isinstance(item, Item):
            item = Item(item)
        if self.includes(item):
            super(Sequence, self).__setitem__(index, item)
            self.__frames = None
            self.__missing = None
        else:
            raise SequenceError("Item is not a member of sequence.")

    def __setslice__(self, start, end, item):
        if isinstance(item, str):
            item = Sequence([item])
        if isinstance(item, list) is False:
            raise TypeError("Invalid type to add to sequence")
        for i in item:
            if self.includes(i) is False:
                raise SequenceError("Item (%s) is not a member of sequence." % i)
        super(Sequence, self).__setslice__(start, end, item)
        self.__frames = None
        self.__missing = None

    def __add__(self, item):
        """return a new sequence with the item appended.  Accepts an Item,
        a string, or a list.
        """
        if isinstance(item, str):
            item = Sequence([item])
        if isinstance(item, list) is False:
            raise TypeError("Invalid type to add to sequence")
        ns = Sequence(self[::])
        ns.extend(item)
        return ns

    def __iadd__(self, item):
        if isinstance(item, str) or isinstance(item, Item):
            item = [item]
        if isinstance(item, list) is False:
            raise TypeError("Invalid type to add to sequence")
        self.extend(item)
        return self

    def format(self, fmt=global_format):
        """Format the stdout string.

        The following directives can be embedded in the format string.
        Format directives support padding, for example: "%04l".

        +-----------+--------------------------------------+
        | Directive | Meaning                              |
        +===========+======================================+
        | ``%s``    | sequence start                       |
        +-----------+--------------------------------------+
        | ``%e``    | sequence end                         |
        +-----------+--------------------------------------+
        | ``%l``    | sequence length                      |
        +-----------+--------------------------------------+
        | ``%f``    | list of found files                  |
        +-----------+--------------------------------------+
        | ``%m``    | list of missing files                |
        +-----------+--------------------------------------+
        | ``%M``    | explicit missingfiles [11-14,19-21]  |
        +-----------+--------------------------------------+
        | ``%p``    | padding, e.g. %06d                   |
        +-----------+--------------------------------------+
        | ``%r``    | implied range, start-end             |
        +-----------+--------------------------------------+
        | ``%R``    | explicit broken range, [1-10, 15-20] |
        +-----------+--------------------------------------+
        | ``%d``    | disk usage                           |
        +-----------+--------------------------------------+
        | ``%H``    | disk usage (human readable)          |
        +-----------+--------------------------------------+
        | ``%D``    | parent directory                     |
        +-----------+--------------------------------------+
        | ``%h``    | string preceding sequence number     |
        +-----------+--------------------------------------+
        | ``%t``    | string after the sequence number     |
        +-----------+--------------------------------------+

        :param fmt: Format string. Default is '%4l %h%p%t %R'.

        :return: Formatted string.
        """
        format_char_types = {
            "s": "i",
            "e": "i",
            "l": "i",
            "f": "s",
            "m": "s",
            "M": "s",
            "p": "s",
            "r": "s",
            "R": "s",
            "d": "s",
            "H": "s",
            "D": "s",
            "h": "s",
            "t": "s",
        }

        atts = self.__attrs__()
        for m in format_re.finditer(fmt):
            var = m.group("var")
            pad = m.group("pad")
            try:
                fmt_char = format_char_types[var]
            except KeyError:
                raise FormatError("Bad directive: %%%s" % var)
            _old = "%s%s" % (pad or "", var)
            _new = "(%s)%s%s" % (var, pad or "", fmt_char)
            fmt = fmt.replace(_old, _new)
            val = atts[var]
            # only execute the callable once, just in case
            if callable(val):
                val = atts[var]()
                atts[var] = val

        return fmt % atts

    @property
    def mtime(self):
        """Returns the latest mtime of all items."""
        maxDate = list()
        for i in self:
            maxDate.append(i.mtime)
        return max(maxDate)

    @property
    def size(self):
        """Returns the size all items in bytes."""
        tempSize = list()
        for i in self:
            tempSize.append(i.size)
        return sum(tempSize)

    @property
    def human(self):
        """Returns the size of all items in human-readable format."""
        total_size = self.size
        units = ["B", "K", "M", "G", "T"]
        unit_index = 0
        while total_size >= 1024 and unit_index < len(units) - 1:
            total_size /= 1024
            unit_index += 1
        return f"{total_size:7.1f}{units[unit_index]}"

    def directory(self):
        return self[0].dirname + os.sep

    def length(self):
        """:return: The length of the sequence."""
        return len(self)

    def frames(self):
        """:return: List of files in sequence."""
        if not hasattr(self, "__frames") or not self.__frames or self.__dirty:
            self.__frames = self._get_frames()
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
        if not hasattr(self, "__missing") or not self.__missing:
            self.__missing = self._get_missing()
        return self.__missing

    def head(self):
        """:return: String before the sequence index number."""
        return self[0].head

    def tail(self):
        """:return: String after the sequence index number."""
        return self[0].tail

    def path(self):
        """:return: Absolute path to sequence."""
        _dirname = str(os.path.dirname(self[0].path))
        return os.path.join(_dirname, str(self))

    def includes(self, item):
        """Checks if the item can be contained in this sequence, i.e. if it
        is a sibling of any of the items in the list.

        For example:

            >>> s = Sequence(['fileA.0001.jpg', 'fileA.0002.jpg'])
            >>> print(s)
            fileA.1-2.jpg
            >>> s.includes('fileA.0003.jpg')
            True
            >>> s.includes('fileB.0003.jpg')
            False

        :param item: pyseq.Item class object.
        :return: True if item is a sequence member.
        """

        if not self:
            return True

        if not isinstance(item, Item):
            item = Item(item)

        if self[-1] != item:
            return self[-1].is_sibling(item)
        elif self[0] != item:
            return self[0].is_sibling(item)
        elif self[0] == item:
            return True

        return False

    def contains(self, item):
        """Checks for sequence membership. Calls Item.is_sibling() and returns
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
            return self.includes(item) and self.end() >= item.frame >= self.start()

        return False

    def append(self, item, check_membership=True):
        """Adds another member to the sequence.

        :param item: pyseq.Item object.
        :param check_membership: Check if `item` is a member. Can be useful if membership
            is checked prior to appending.
        :exc:`SequenceError` raised if item is not a sequence member.
        """

        if not isinstance(item, Item):
            item = Item(item)

        if not check_membership:
            super(Sequence, self).append(item)
        else:
            if self.includes(item):
                super(Sequence, self).append(item)
            else:
                raise SequenceError(f"Item {item} is not a member of this sequence.")

    def insert(self, index, item, check_membership=True):
        """Add another member to the sequence at the given index.

        :param item: pyseq.Item object.
        :param check_membership: Check if `item` is a member. Can be useful if membership
            is checked prior to appending.
        :exc: `SequenceError` Raised if item is not a sequence member.
        """

        if not isinstance(item, Item):
            item = Item(item)

        if not check_membership:
            super(Sequence, self).insert(index, item)
        else:
            if self.includes(item):
                super(Sequence, self).insert(index, item)
            else:
                raise SequenceError(f"Item {item} is not a member of this sequence.")

    def extend(self, items, check_membership=True):
        """Add members to the sequence.

        :param items: List of pyseq.Item objects.
        :param check_membership: Check if `item` is a member. Can be useful if membership
            is checked prior to appending.
        :exc: `SequenceError` Raised if any items are not a sequence member.
        """

        for item in items:
            self.append(item, check_membership=check_membership)

    def reIndex(self, offset, padding=None):
        """Renames and reindexes the items in the sequence, e.g. ::

            >>> seq.reIndex(offset=100)

        will add a 100 frame offset to each Item in `seq`, and rename
        the files on disk.

        :param offset: The frame offset to apply to each item.
        :param padding: Change the padding.
        """

        if not padding:
            padding = self.format("%p")

        if offset > 0:
            gen = (
                (image, frame)
                for (image, frame) in zip(reversed(self), reversed(self.frames()))
            )
        else:
            gen = ((image, frame) for (image, frame) in zip(self, self.frames()))

        for image, frame in gen:
            oldName = image.path
            newFrame = padding % (frame + offset)
            newFileName = "%s%s%s" % (self.format("%h"), newFrame, self.format("%t"))
            newName = os.path.join(image.dirname, newFileName)

            try:
                import shutil

                shutil.move(oldName, newName)
            except Exception as err:
                warnings.warn(
                    "%s during reIndex %s -> %s: \n%s"
                    % (
                        err.__class__.__name__,
                        oldName,
                        newName,
                        traceback.format_exc(),
                    )
                )
            else:
                self.__dirty = True
                image.frame = int(newFrame)

        else:
            self.frames()

    def _get_padding(self):
        """:return: Padding string (e.g. %07d)."""
        try:
            pad = min([i.pad for i in self])
            if pad is None:
                return ""
            if pad < 2:
                return "%d"
            return "%%%02dd" % pad
        except IndexError:
            return ""

    def _get_framerange(self, frames, missing=True):
        """Returns frame range string, e.g. [1-500].

        :param frames: List of ints like [1,4,8,12,15].
        :param missing: Expand sequence to exclude missing sequence indices.
        :return: Formatted frame range string.
        """

        frange = []
        start = ""
        end = ""
        if not missing:
            if frames:
                return "%s-%s" % (self.start(), self.end())
            else:
                return ""

        if not frames:
            return ""

        for i in range(0, len(frames)):
            frame = frames[i]
            if isinstance(frame, range):
                frange.append("%s-%s" % (frame[0], frame[-1]))
                continue
            prev = frames[i - 1]
            if i != 0 and frame != prev + 1:
                if start != end:
                    frange.append("%s-%s" % (str(start), str(end)))
                elif start == end:
                    frange.append(str(start))
                start = end = frame
                continue
            if start == "" or int(start) > frame:
                start = frame
            if end == "" or int(end) < frame:
                end = frame
        if start == end:
            frange.append(str(start))
        else:
            frange.append("%s-%s" % (str(start), str(end)))
        return "[%s]" % range_join.join(frange)

    def _get_frames(self):
        """Finds the sequence indexes from item names."""
        return [f.frame for f in self if f.frame is not None]

    def _get_missing(self, max_size=100000):
        """Looks for missing sequence indexes in the sequence.

        :param max_size: maximum missing frame sequence size for
            returning explcit frames, otherwise use ranges.
        :return: List of missing frames, or ranges of frames if
            sequence size is greater than max_size.
        """

        missing = []
        frames = self.frames()

        if len(frames) == 0:
            return missing
        elif len(frames) == 1:
            return frames

        r = range(frames[0], frames[-1] + 1)
        if len(r) <= max_size:
            frames_set = set(frames)
            r_set = set(r)
            symmetric_diff = frames_set.symmetric_difference(r_set)
            return sorted(symmetric_diff)
        else:
            for i, f in enumerate(frames[:-1]):
                missing.append(range(f + 1, frames[i + 1]))
            return missing


def diff(f1, f2):
    """Examines diffs between f1 and f2 and deduces numerical sequence number.

    For example ::

        >>> diff('file01_0040.rgb', 'file01_0041.rgb')
        [{'frames': ('0040', '0041'), 'start': 7, 'end': 11}]

        >>> diff('file3.03.rgb', 'file4.03.rgb')
        [{'frames': ('3', '4'), 'start': 4, 'end': 5}]

    :param f1: pyseq.Item object.
    :param f2: pyseq.Item object to diff.
    :return: A dictionary with keys 'frames', 'start', and 'end'.
    """

    if not isinstance(f1, Item):
        f1 = Item(f1)
    if not isinstance(f2, Item):
        f2 = Item(f2)

    d = []
    if len(f1.number_matches) == len(f2.number_matches):
        for m1, m2 in zip(f1.number_matches, f2.number_matches):
            if (m1.start() == m2.start()) and (m1.group() != m2.group()):
                if strict_pad is True and (len(m1.group()) != len(m2.group())):
                    continue
                d.append(
                    {
                        "start": m1.start(),
                        "end": m1.end(),
                        "frames": (m1.group(), m2.group()),
                    }
                )

    return d


def uncompress(seq_string, fmt=global_format):
    """Basic uncompression or deserialization of a compressed sequence string.

    For example: ::

        >>> seq = uncompress('./tests/files/012_vb_110_v001.%04d.png 1-10', fmt='%h%p%t %r')
        >>> print(seq)
        012_vb_110_v001.1-10.png
        >>> len(seq)
        10
        >>> seq2 = uncompress('./tests/files/a.%03d.tga [1-3, 10, 12-14]', fmt='%h%p%t %R')
        >>> print(seq2)
        a.1-14.tga
        >>> len(seq2)
        7
        >>> seq3 = uncompress('a.%03d.tga 1-14 ([1-3, 10, 12-14])', fmt='%h%p%t %r (%R)')
        >>> print(seq3)
        a.1-14.tga
        >>> len(seq3)
        7

    See unit tests for more examples.

    :param seq_string: Compressed sequence string.
    :param fmt: Format of sequence string.
    :return: :class:`.Sequence` instance.
    """

    dirname = os.path.dirname(seq_string)

    # remove directory
    if "%D" in fmt:
        fmt = fmt.replace("%D", "")
    name = os.path.basename(seq_string)

    # map of directives to regex
    remap = {
        "s": r"\d+",
        "e": r"\d+",
        "l": r"\d+",
        "h": r"(\S+)?",
        "t": r"(\S+)?",
        "r": r"\d+-\d+",
        "R": r"\[[\d\s?\-%s?]+\]" % re.escape(range_join),
        "p": r"%\d+d",
        "m": r"\[.*\]",
        "f": r"\[.*\]",
    }

    # escape any re chars in format
    fmt = re.escape(fmt)

    # replace \% with % back again
    fmt = fmt.replace("\\%", "%")

    for m in format_re.finditer(fmt):
        _old = "%%%s%s" % (m.group("pad") or "", m.group("var"))
        _new = "(?P<%s>%s)" % (m.group("var"), remap.get(m.group("var"), r"\w+"))
        fmt = fmt.replace(_old, _new)

    regex = re.compile(fmt)
    match = regex.match(name)

    frames = []
    missing = []
    s = None
    e = None

    if not match:
        return

    try:
        pad = match.group("p")

    except IndexError:
        pad = "%d"

    try:
        R = match.group("R")
        R = R[1:-1]
        number_groups = R.split(range_join)
        pad_len = 0
        for number_group in number_groups:
            if "-" in number_group:
                splits = number_group.split("-")
                pad_len = max(pad_len, len(splits[0]), len(splits[1]))
                start = int(splits[0])
                end = int(splits[1])
                frames.extend(range(start, end + 1))

            else:
                end = int(number_group)
                pad_len = max(pad_len, len(number_group))
                frames.append(end)
        if pad == "%d" and pad_len != 0:
            pad = "%0" + str(pad_len) + "d"

    except IndexError:
        try:
            r = match.group("r")
            s, e = r.split("-")
            frames = range(int(s), int(e) + 1)

        except IndexError:
            s = match.group("s")
            e = match.group("e")

    try:
        frames = eval(match.group("f"))

    except IndexError:
        pass

    try:
        missing = eval(match.group("m"))

    except IndexError:
        pass

    items = []
    if missing:
        for i in range(int(s), int(e) + 1):
            if i in missing:
                continue
            f = pad % i
            name = "%s%s%s" % (
                match.groupdict().get("h", ""),
                f,
                match.groupdict().get("t", ""),
            )
            items.append(Item(os.path.join(dirname, name)))

    else:
        for i in frames:
            f = pad % i
            name = "%s%s%s" % (
                match.groupdict().get("h", ""),
                f,
                match.groupdict().get("t", ""),
            )
            items.append(Item(os.path.join(dirname, name)))

    seqs = get_sequences(items)
    if seqs:
        return seqs[0]
    return seqs


def get_sequences(source):
    """Returns a list of Sequence objects given a directory or list that contain
    sequential members.

    Get sequences in a directory:

        >>> seqs = get_sequences('tests/files/')
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

        >>> seqs = get_sequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
        >>> for s in seqs: print(s)
        ...
        fileA.1-2.rgb
        fileB.1.rgb

    :param source: Can be directory path, list of strings, or sortable list of objects.
    :return: List of pyseq.Sequence class objects.
    """

    seqs = []

    if isinstance(source, list):
        items = sorted(source, key=lambda x: str(x))

    elif isinstance(source, str):
        if os.path.isdir(source):
            items = sorted(glob(os.path.join(source, "*")))
        else:
            items = sorted(glob(source))

    else:
        raise TypeError("Unsupported format for source argument")

    items = deque(items)

    # organize the items into sequences
    while items:
        item = Item(items.popleft())
        found = False
        for seq in reversed(seqs):
            if seq.includes(item):
                seq.append(item, check_membership=False)
                found = True
                break
        if not found:
            seq = Sequence([item])
            seqs.append(seq)

    return seqs


def iget_sequences(source):
    """Generator version of get_sequences.  Creates Sequences from a various
    source files.  A notable difference is the sort order of iget_sequences
    versus get_sequences.  iget_sequences uses an adaption of natural sorting
    that starts with the file extension.  Because of this, Sequences are
    returned ordered by their file extension.

    Get sequences in a directory:

        >>> seqs = iget_sequences('./tests/files/')
        >>> for s in seqs: print(s)
        ...
        file01.1-4.j2k
        fileA.1-3.jpg
        012_vb_110_v001.1-10.png
        012_vb_110_v002.1-10.png
        fileA.1-3.png
        z1_001_v1.1-4.png
        z1_002_v1.1-4.png
        z1_002_v2.1-4.png
        file1.03.rgb
        file01_40-43.rgb
        file2.03.rgb
        file02_44-47.rgb
        file3-4.03.rgb
        file.info.03.rgb
        a.1-14.tga
        bnc01_TinkSO_tx_0_ty_0.101-105.tif
        bnc01_TinkSO_tx_0_ty_1.101-105.tif
        bnc01_TinkSO_tx_1_ty_0.101-105.tif
        bnc01_TinkSO_tx_1_ty_1.101-105.tif
        file.1-2.tif
        file_02.tif
        alpha.txt

    Get sequences from a list of file names:

        >>> seqs = iget_sequences(['fileA.1.rgb', 'fileA.2.rgb', 'fileB.1.rgb'])
        >>> for s in seqs: print(s)
        ...
        fileA.1-2.rgb
        fileB.1.rgb

    :param source: Can be directory path, list of strings, or sortable list of objects.
    :return: List of pyseq.Sequence class objects.
    """

    if isinstance(source, list):
        items = source
    elif isinstance(source, str):
        if os.path.isdir(source):
            join = os.path.join
            items = [join(source, x) for x in os.listdir(source)]
        else:
            items = iglob(source)
    else:
        raise TypeError("Unsupported format for source argument")

    items = deque(sorted(items, key=_ext_key))

    seq = None
    while items:
        item = Item(items.popleft())
        if seq is None:
            seq = Sequence([item])
        elif seq.includes(item):
            seq.append(item, check_membership=False)
        else:
            yield seq
            seq = Sequence([item])

    if seq is not None:
        yield seq


def walk(source, level=-1, topdown=True, onerror=None, followlinks=False, hidden=False):
    """Generator that traverses a directory structure starting at
    source looking for sequences.

    :param source: Valid folder path to traverse.
    :param level: int, if < 0 traverse entire structure otherwise traverse to given depth.
    :param topdown: Walk from the top down.
    :param onerror: Callable to handle os.listdir errors.
    :param followlinks: Whether to follow links.
    :param hidden: Include hidden files and dirs.
    """

    for root, dirs, files in os.walk(source, topdown, onerror, followlinks):
        if not hidden:
            files = [f for f in files if not f[0] == "."]
            dirs[:] = [d for d in dirs if not d[0] == "."]

        files = [os.path.join(root, f) for f in files]

        if topdown is True:
            parts = root.replace(source, "").split(os.sep)
            while "" in parts:
                parts.remove("")
            if len(parts) == level - 1:
                del dirs[:]

        yield root, dirs, get_sequences(files)
