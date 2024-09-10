#!/usr/bin/env python
#
# Copyright (c) 2024, Ryan Galloway (ryan@rsgalloway.com)
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
#

__doc__ = """
Contains default configs and settings.
"""

import os
import re
import sys
import platform

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

DEBUG = os.getenv("DEBUG")
LOG_LEVEL = int(os.environ.get("LOG_LEVEL", 20))
ON_POSIX = "posix" in sys.builtin_module_names
PLATFORM = platform.system().lower()
PYTHON_VERSION = sys.version_info[0]
