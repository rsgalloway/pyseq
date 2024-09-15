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
Contains the main lss function for the pyseq module.
"""

import glob
import optparse
import os
import sys

from pyseq import __version__, get_sequences
from pyseq import seq as pyseq
from pyseq import walk


def tree(source, level, seq_format):
    """Recusrively walk from the source and display all the the folders and
    sequences.
    """

    if sys.stdout.isatty():
        blue = "\033[94m"
        endc = "\033[0m"
    else:
        blue = ""
        endc = ""
    ends = {}
    done = []

    print("{0}{1}".format(blue, os.path.relpath(source)))

    for root, dirs, seqs in walk(source, level):
        if len(dirs) > 0:
            ends[root] = dirs[-1]
        else:
            ends[root] = None

        sp = ""
        if root != sorted(source):
            p = root
            while p != source:
                dir_name, base = os.path.split(p)
                if dir_name == source:
                    break
                elif dir_name in done:
                    sp = "    " + sp
                elif ends[dir_name] != base:
                    sp = "│   " + sp
                elif ends[dir_name] == base:
                    sp = "│   " + sp
                else:
                    sp = "    " + sp
                p = dir_name

        base = os.path.basename(root)
        if root == source:
            pass
        elif ends[os.path.dirname(root)] == base:
            print("".join([sp, "└── ", "%s%s%s" % (blue, base, endc)]))
            done.append(root)
            ends[os.path.dirname(root)] = None
            sp += "    "
        else:
            print("".join([sp, "├── ", "%s%s%s" % (blue, base, endc)]))
            sp += "│   "

        sequence_length = len(seqs)
        for i, seq in enumerate(seqs):
            if i == (sequence_length - 1) and len(dirs) == 0:
                print("".join([sp, "└── ", seq.format(seq_format)]))
            else:
                print("".join([sp, "├── ", seq.format(seq_format)]))
    print(endc)


def _recur_cb(option, opt_str, value, parser):
    """Callback for the `recursive` argument."""
    if value is None:
        value = -1
    else:
        value = int(value)
    setattr(parser.values, option.dest, value)


def main():
    """Command-line interface."""

    usage = (
        """
lss [path] [-f format] [-d] [-r]

Formatting options:

    You can format the output of lss using the --format option and passing
    in a format string.

    Default format string is "%s"

    Supported directives:
        %%s   sequence start
        %%e   sequence end
        %%l   sequence length
        %%f   list of found files
        %%m   list of missing files
        %%p   padding, e.g. %%06d
        %%r   absolute range, start-end
        %%R   expanded range, start-end [missing]
        %%d   disk usage
        %%h   string preceding sequence number
        %%t   string after the sequence number

    Format directives support padding, for example: "%%04l".
    """
        % pyseq.global_format
    )

    parser = optparse.OptionParser(usage=usage, version="%prog " + __version__)
    parser.add_option(
        "-f", "--format", dest="format", default=None, help="format the output string"
    )
    parser.add_option(
        "-r",
        "--recursive",
        dest="recursive",
        action="callback",
        callback=_recur_cb,
        help="Walks the entire directory structure.",
    )
    parser.add_option(
        "-s",
        "--strict",
        dest="strict",
        action="store_true",
        default=pyseq.strict_pad,
        help="strict padding (default false)",
    )
    (options, args) = parser.parse_args()

    pyseq.strict_pad = options.strict

    if len(args) == 0:
        args = [os.getcwd()]

    items = []
    for path in args:
        if os.path.isdir(path):
            join = os.path.join
            items = [join(path, x) for x in os.listdir(path)]
        else:
            items.extend(glob.glob(path))

    if options.recursive is None:
        for seq in get_sequences(items):
            print(seq.format(options.format or pyseq.global_format))
    else:
        level = options.recursive
        for path in args:
            path = os.path.abspath(path.rstrip(os.sep))
            if not os.path.isdir(path):
                continue
            tree(path, level, options.format or "%h%r%t")

    return 0


if __name__ == "__main__":
    sys.exit(main())
