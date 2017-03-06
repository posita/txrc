.. -*- encoding: utf-8; mode: rst -*-
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>>> IMPORTANT: READ THIS BEFORE EDITING! <<<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    Please keep each sentence on its own unwrapped line.
    It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
    Thank you!

.. toctree::
    :maxdepth: 3
    :hidden:

Copyright and other protections apply.
Please see the accompanying :doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If those files are missing or appear to be modified from their originals, then please contact the author before viewing or using this software in any capacity.

Introduction
============

``txrc`` is a :doc:`pure Python module <modules>` for retrying calls in `Twisted`_.
It is based on `Terry Jones's proposal <http://blogs.fluidinfo.com/terry/2009/11/12/twisted-code-for-retrying-function-calls/>`__.

.. _`Twisted`: https://twistedmatrix.com/

License
-------

``txrc`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the :doc:`LICENSE <LICENSE>` file for details.
Source code is `available on GitHub <https://github.com/posita/txrc>`__.

Installation
------------

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/txrc/>`__):

.. code-block:: console

    % pip install txrc
    ...

Alternately, you can download the sources (e.g., `from GitHub <https://github.com/posita/txrc>`__) and run ``setup.py``:

.. code-block:: console

    % git clone https://github.com/posita/txrc
    ...
    % cd txrc
    % python setup.py install
    ...

Requirements
------------

The service you want to consume must use v1.x of the Socket.IO protocol. Earlier versions are not supported.

A modern version of Python is required:

*   `cPython <https://www.python.org/>`_ (2.7 or 3.3+)

*   `PyPy <http://pypy.org/>`_ (Python 2.7 or 3.3+ compatible)

Python 2.6 will *not* work.

``txrc`` has the following dependencies (which will be installed automatically):

*   |Twisted|_
*   |future|_

.. |Twisted| replace:: ``Twisted``
.. _`Twisted`: https://twistedmatrix.com/
.. |future| replace:: ``future``
.. _`future`: http://python-future.org/
