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

Copyright |(c)| 2015 `Matt Bogosian`_ (|@posita|_).

.. |(c)| unicode:: u+a9
.. _`Matt Bogosian`: mailto:mtb19@columbia.edu?Subject=txrc
.. |@posita| replace:: **@posita**
.. _`@posita`: https://github.com/posita

Please see the accompanying |LICENSE|_ (or |LICENSE.txt|_) file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If such a file did not accompany this software, then please contact the author before viewing or using this software in any capacity.

.. |LICENSE| replace:: ``LICENSE``
.. _`LICENSE`: _sources/LICENSE.txt
.. |LICENSE.txt| replace:: ``LICENSE.txt``
.. _`LICENSE.txt`: _sources/LICENSE.txt

Introduction
============

``txrc`` is a :doc:`pure Python module <modules>` for retrying calls in `Twisted`_.
It is based on `Terry Jones's proposal <http://blogs.fluidinfo.com/terry/2009/11/12/twisted-code-for-retrying-function-calls/>`__.

.. _`Twisted`: https://twistedmatrix.com/

License
-------

``txrc`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
Source code is `available on GitHub <https://github.com/posita/txrc>`__.

Installation
------------

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/txrc/>`__):

.. code-block:: sh

    % pip install txrc
    ...

Alternately, you can download the sources (e.g., `from GitHub <https://github.com/posita/txrc>`__) and run ``setup.py``:

.. code-block:: sh

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

*   |future|_

*   |twisted|_

.. |future| replace:: ``future``
.. _`future`: http://python-future.org/
.. |twisted| replace:: ``twisted``
.. _`twisted`: https://twistedmatrix.com/
