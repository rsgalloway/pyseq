#!/usr/bin/env python
#
# Copyright (c) 2011-2025, Ryan Galloway (ryan@rsgalloway.com)
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
Contains pyseq configs and default settings.
"""

import os
import re

# default serialization format string
DEFAULT_FORMAT = "%h%r%t"
default_format = os.getenv("PYSEQ_DEFAULT_FORMAT", DEFAULT_FORMAT)

# default serialization format string for global sequences
DEFAULT_GLOBAL_FORMAT = "%4l %h%p%t %R"
global_format = os.getenv("PYSEQ_GLOBAL_FORMAT", DEFAULT_GLOBAL_FORMAT)

# use strict padding on sequences (pad length must match)
PYSEQ_STRICT_PAD = os.getenv("PYSEQ_STRICT_PAD", 0)
PYSEQ_NOT_STRICT = os.getenv("PYSEQ_NOT_STRICT", 1)
strict_pad = int(PYSEQ_STRICT_PAD) == 1 or int(PYSEQ_NOT_STRICT) == 0

# regex pattern for matching all numbers in a filename
digits_re = re.compile(r"\d+")

# regex pattern for matching frame numbers only
# the default is \d+ for maximum compatibility
DEFAULT_FRAME_PATTERN = r"\d+"
frames_re = re.compile(os.environ.get("PYSEQ_FRAME_PATTERN", DEFAULT_FRAME_PATTERN))

# regex for matching format directives
format_re = re.compile(r"%(?P<pad>\d+)?(?P<var>\w+)")

# character to join explicit frame ranges on
DEFAULT_RANGE_SEP = ", "
range_join = os.getenv("PYSEQ_RANGE_SEP", DEFAULT_RANGE_SEP)
