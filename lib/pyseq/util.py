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

import functools
import os
import re
import warnings


def deprecated(func):
    """Deprecation warning decorator."""

    def inner(*args, **kwargs):
        warnings.warn(
            "Call to deprecated method {}".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    inner.__name__ = func.__name__
    inner.__doc__ = func.__doc__
    inner.__dict__.update(func.__dict__)
    return inner


def _natural_key(x):
    """Splits a string into characters and digits.

    :param x: The string to be split.
    :return: A list of characters and digits.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", x)]


def _ext_key(x):
    """Similar to `_natural_key` except this one uses the file extension at
    the head of split string.  This fixes issues with files that are named
    similar but with different file extensions:

    This example:

        file.001.jpg
        file.001.tiff
        file.002.jpg
        file.002.tiff

    Would get properly sorted into:

        file.001.jpg
        file.002.jpg
        file.001.tiff
        file.002.tiff
    """
    name, ext = os.path.splitext(x)
    return [ext] + _natural_key(name)


@functools.lru_cache(maxsize=None)
def natural_sort(items):
    """
    Sorts a list of items in natural order.

    :param items: The list of items to be sorted.
    :return: The sorted list of items.
    """
    return sorted(items, key=_natural_key)
