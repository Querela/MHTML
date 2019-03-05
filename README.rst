MHTML Utils
===========

.. start-badges

.. image:: https://travis-ci.org/Querela/MHTML.svg?branch=master
   :alt: MHTML build status on Travis CI
   :target: https://travis-ci.org/Querela/MHTML

.. image:: https://coveralls.io/repos/github/Querela/MHTML/badge.svg?branch=master
   :alt: MHTML code coverage on Coveralls
   :target: https://coveralls.io/github/Querela/MHTML?branch=master

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
It contains severals example scripts to show how the package can be used.

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
