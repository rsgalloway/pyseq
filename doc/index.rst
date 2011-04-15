.. PySeq documentation master file, created by
   sphinx-quickstart on Sat Mar 12 19:28:34 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===========================
PySeq v0.2.1b documentation
===========================

PySeq is a python module that finds groups of items that follow a naming convention containing a numerical sequence index (e.g. fileA.001.png, fileA.002.png, fileA.003.png...) and serializes them into a compressed sequence string representing the entire sequence (e.g. fileA.1-3.png). It should work regardless of where the numerical sequence index is embedded in the name. For examples, see basic usage below.

Installation
============

Installing PySeq is easily done using
`setuptools`_. Assuming it is
installed, just run the following from the command-line:

.. sourcecode:: none

    $ easy_install pyseq

* `setuptools`_
* `install setuptools <http://peak.telecommunity.com/DevCenter/EasyInstall#installation-instructions>`_

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

Alternatively, you can install from the distribution using the ``setup.py``
script:

.. sourcecode:: none

    $ python setup.py install

Overview
========

PySeq comes with a command-line script called ``lss``. 

.. sourcecode:: none

    $ lss [path] [-f format] [-d]

Using the "z1" file sequence example in the "tests" directory:

::

	% ls tests/z1*
	tests/z1_001_v1.1.png	tests/z1_001_v1.4.png	tests/z1_002_v1.3.png	tests/z1_002_v2.2.png
	tests/z1_001_v1.2.png	tests/z1_002_v1.1.png	tests/z1_002_v1.4.png	tests/z1_002_v2.3.png
	tests/z1_001_v1.3.png	tests/z1_002_v1.2.png	tests/z1_002_v2.1.png	tests/z1_002_v2.4.png

	% lss tests/z1*
	   4 z1_001_v1.%d.png 1-4
	   4 z1_002_v1.%d.png 1-4
	   4 z1_002_v2.%d.png 1-4

	% lss tests/z1* -f "%h%r%t"
	z1_001_v1.1-4.png
	z1_002_v1.1-4.png
	z1_002_v2.1-4.png

Some API usage examples
***********************

**Sequence compression**

*Example using getSequences to compress filesystem sequences starting with "bnc". The getSequences function will return a list of all sequences found using the given input, which can be either a path or a list.*

	>>> from pyseq import *
	>>> seqs = getSequences('./tests/bnc*')
	>>> for s in seqs: print s.format('%h%p%t %r')
	... 
	bnc01_TinkSO_tx_0_ty_0.%04d.tif 101-105
	bnc01_TinkSO_tx_0_ty_1.%04d.tif 101-105
	bnc01_TinkSO_tx_1_ty_0.%04d.tif 101-105
	bnc01_TinkSO_tx_1_ty_1.%04d.tif 101-105

*Example using the Sequence class with a list as input. The Sequence class constructor will return a single Sequence class instance of sequential items, skipping any items in the list that are not part of the sequence.*

	>>> s = Sequence(['file.0001.jpg', 'file.0002.jpg', 'file.0003.jpg'])
	>>> print s
	file.1-3.jpg
	>>> s.append('file.0006.jpg')
	>>> print s.format("%h%p%t %R")
	file.%04d.jpg 1-3 6
	>>> s.contains('file.0009.jpg')
	True
	>>> s.contains('file.0009.pic')
	False
	
**Sequence expansion**
	
	>>> s = uncompress('012_vb_110_v002.1-150.dpx', format="%h%r%t")
	>>> len(s)
	150
	>>> seq = uncompress('./tests/012_vb_110_v001.%04d.png 1-10', format='%h%p%t %r')
	>>> print seq.format('%04l %h%p%t %R')
	  10 012_vb_110_v001.%04d.png 1-10
	
Source Code
===========

PySeq's git repo is available on GitHub, which can be browsed at:

 * https://github.com/rsgalloway/pyseq

and cloned using::

	$ git clone git://github.com/rsgalloway/pyseq.git pyseq

API Reference
=============

.. toctree::
   :maxdepth: 2

.. automodule:: pyseq
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

