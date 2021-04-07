#!/usr/bin/env python
#
# Copyright (C) 2011-2021 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Shotman and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

from distutils.core import setup
from pyseq import __version__

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='pyseq',
    version=__version__,
    description='Compressed Sequence String Module',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Ryan Galloway',
    author_email='ryan@rsgalloway.com',
    url='http://github.com/rsgalloway/pyseq',
    py_modules=['pyseq'],
    scripts = ['lss']
)
