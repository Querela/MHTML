MHTML Utils
===========

.. start-badges

.. image:: https://travis-ci.org/Querela/MHTML.svg?branch=master
   :alt: MHTML build status on Travis CI
   :target: https://travis-ci.org/Querela/MHTML

.. image:: https://coveralls.io/repos/github/Querela/MHTML/badge.svg?branch=master
   :alt: MHTML code coverage on Coveralls
   :target: https://coveralls.io/github/Querela/MHTML?branch=master

.. image:: https://img.shields.io/github/release/Querela/MHTML.svg
   :alt: GitHub release
   :target: https://github.com/Querela/MHTML/releases/latest

.. image:: https://img.shields.io/github/languages/code-size/Querela/MHTML.svg
   :alt: GitHub code size in bytes
   :target: https://github.com/Querela/MHTML/archive/master.zip

.. image:: https://img.shields.io/github/license/Querela/MHTML.svg
   :alt: MHTML License
   :target: https://github.com/Querela/MHTML/blob/master/LICENSE

.. end-badges

Copyright (c) 2019 Querela.  All rights reserved.

See the end of this file for further copyright and license information.

* Free software: MIT license

This package contains MHTML utilities for working with **Chrome**/**Chromium**
*Blink* saved webarchives in the .mhtml format.
It may later also be able to work with any ``.mht``, ``.mhtm`` / ``.mhtml``
files but currently strictly refers to the Blink implementation. See:
`Chromium Blink on Github <https://github.com/chromium/chromium/blob/master/third_party/blink/renderer/platform/mhtml/>`_ or
`Chromium Blink on GoogleSource <https://chromium.googlesource.com/chromium/src/third_party/+/master/blink/renderer/platform/mhtml/>`_,
`Chromium Blink.git on GoogleSource <https://chromium.googlesource.com/chromium/blink.git/+/master/Source/platform/mhtml/>`_.

This package was developed because the ``MIME`` / `email <https://docs.python.org/3/library/email.html>`_
utilities of the standard Python library were mangling binary content,
e. g. in images.
It tried to convert ``\r`` and ``\n`` linebreak characters according to some
policy. Trying to switch or disable this behaviour was not successful.
This package will not work for any ``MIME`` message but tries to be completely
save for using with MHTML files saved by the Blink engine *(?)*.

This package doesn't currently try to fully parse the MHTML file but rather
provide a view onto the raw binary content. Extracting a resource is only
getting a slice between two different offsets. The header detection should
work for almost any MHTML data but I will have to try different input files
from other sources to be sure.

This package contains severals example scripts to show how the package can be
used. That include dumping embedded resources into a directory, extracting
the main web page or listing all the resources in a MHTML archive.
It also allows to remove existing resources from an MHTML file, e. g. for
stripping adverts, images etc. as well as inserting new resources from another
MHTML file. (Later it may be possible to create resources from any file.)

Since Chrome disables javascript and strips all unneccessary content from a
newly created MHTML file, it is not really possible to make an interactive
MHTML file containing a directory and linked pages. Work in progress is the
ability to alter a resource so that client scripts can be written to combine
multiple MHTML files into a single one and display the whole content.

It may later also be possible to create a MHTML archive from a given list or
description but is not the priority.

.. contents::

General Information
-------------------

- Website: https://github.com/Querela/MHTML
- Source code: https://github.com/Querela/MHTML
- Issue tracker: https://github.com/Querela/MHTML/issues
- Documentation: WIP

Installation
------------

This project requires at least Python 3.5. It has no other dependencies.

Development
-----------

To work with the source and run test with ``py.test`` etc. it offers several
development dependencies that can be installed:

::

    pip install -e .[dev]

Tests can be run with:

::

    python setup.py test

Run stylechecks:

::

    python setup.py flake8
    python setup.py pylint

Clean up:

::

    python setup.py clean --all

Copyright and License Information
---------------------------------

Copyright (c) 2019 Querela.  All rights reserved.

See the file "LICENSE" for information on the history of this software, terms &
conditions for usage, and a DISCLAIMER OF ALL WARRANTIES.

All trademarks referenced herein are property of their respective holders.
