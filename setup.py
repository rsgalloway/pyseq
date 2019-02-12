#!/usr/bin/env python
#
# Copyright (C) 2011-2018 Ryan Galloway (ryangalloway.com)
#
# This module is part of PySeq and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import setuptools
from distutils.core import setup
from pyseq import __version__

setup(
    name='pyseq',
    version=__version__,
    description='Compressed Sequence String Module',
    author='Ryan Galloway',
    author_email='ryan@rsgalloway.com',
    url='http://github.com/rsgalloway/pyseq',
    py_modules=['pyseq'],
    scripts=['lss']
)
