PySeq
=====

PySeq is a python module that finds groups of items that follow a naming convention containing 
a numerical sequence index (e.g. fileA.001.png, fileA.002.png, fileA.003.png...) and serializes
them into a compressed sequence string representing the entire sequence (e.g. fileA.1-3.png). It 
should work regardless of where the numerical sequence index is embedded in the name. For examples,
see basic usage below or http://rsgalloway.github.io/pyseq

Installation
------------

Installation using setuputils: ::

  % pip install pyseq


Basic Usage
-----------

Using the "z1" file sequence example in the "tests" directory, we start by listing the directory
contents using ``ls``. ::

    $ ls tests/files/z1*
    tests/files/z1_001_v1.1.png tests/files/z1_002_v1.3.png
    tests/files/z1_001_v1.2.png tests/files/z1_002_v1.4.png
    tests/files/z1_001_v1.3.png tests/files/z1_002_v2.1.png
    tests/files/z1_001_v1.4.png tests/files/z1_002_v2.2.png
    tests/files/z1_002_v1.1.png tests/files/z1_002_v2.3.png
    tests/files/z1_002_v1.2.png tests/files/z1_002_v2.4.png

Now we list the same directory contents using `lss`, which will find the sequences and display them
in the default compressed format. ::

    $ lss tests/files/z1*
       4 z1_001_v1.%d.png [1-4]
       4 z1_002_v1.%d.png [1-4]
       4 z1_002_v2.%d.png [1-4]

... with a custom format: ::

    $ lss tests/files/z1* -f "%h%r%t"
    z1_001_v1.1-4.png
    z1_002_v1.1-4.png
    z1_002_v2.1-4.png

... recursive: ::

    $ lss -r tests
    tests
    ├── test_pyseq.py
    └── files
        ├── 012_vb_110_v001.1-10.png
        └── 012_vb_110_v002.1-10.png


API Examples
------------

Compression, or serialization, of lists of items ::

    >>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
    >>> print s
    file.1-3.jpg
    >>> s.append('file.0006.jpg')
    >>> print(s.format("%h%p%t %R"))
    file.%04d.jpg [1-3, 6]
    >>> s.contains('file.0009.jpg')
    True
    >>> s.contains('file.0009.pic')
    False

Uncompression, or deserialization, of compressed sequences strings ::

    >>> s = uncompress('012_vb_110_v002.1-150.dpx', format="%h%r%t")
    >>> len(s)
    150
    >>> seq = uncompress('./tests/012_vb_110_v001.%04d.png 1-10', format='%h%p%t %r')
    >>> print(seq.format('%04l %h%p%t %R'))
      10 012_vb_110_v001.%04d.png [1-10]

