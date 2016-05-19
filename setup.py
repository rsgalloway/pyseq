#!/usr/bin/env python
#
# Copyright (C) 2011-2016 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Shotman and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

from distutils.core import setup
from pyseq import __version__
setup(
    name='pyseq',
    version=__version__,
    description='Compressed Sequence Python Module',
    author='Ryan Galloway',
    author_email='ryan@rsgalloway.com',
    url='http://github.com/rsgalloway/pyseq',
    py_modules=['pyseq'],
    scripts = ['lss']
)
