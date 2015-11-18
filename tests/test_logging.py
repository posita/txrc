#!/usr/bin/env python
#-*- encoding: utf-8; grammar-ext: py; mode: python -*-

#=========================================================================
"""
  Copyright |(c)| 2015 `Matt Bogosian`_ (|@posita|_).

  .. |(c)| unicode:: u+a9
  .. _`Matt Bogosian`: mailto:mtb19@columbia.edu
  .. |@posita| replace:: **@posita**
  .. _`@posita`: https://github.com/posita

  Please see the accompanying ``LICENSE`` (or ``LICENSE.txt``) file for
  rights and restrictions governing use of this software. All rights not
  expressly waived or licensed are reserved. If such a file did not
  accompany this software, then please contact the author before viewing
  or using this software in any capacity.
"""
#=========================================================================

from __future__ import (
    absolute_import, division, print_function, unicode_literals,
)
from builtins import * # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import * # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

#---- Imports ------------------------------------------------------------

import logging
import os
import sys
from twisted.internet import defer as t_defer
from twisted.trial import unittest as t_unittest

from txrc.logging import (
    logerrbackdl,
    logunhandlederr,
)
import tests # pylint: disable=unused-import
from tests.symmetries import mock

#---- Constants ----------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

#---- Classes ------------------------------------------------------------

#=========================================================================
class LoggingTestCase(t_unittest.TestCase):

    longMessage = True

    #---- Public hooks ---------------------------------------------------

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_logunhandlederr(self):
        logger = mock.Mock()
        _raiseorreturn = logunhandlederr(logging.DEBUG, logger)(self._raiseorreturn)

        logger.reset_mock()
        success_d = _raiseorreturn()
        self.assertTrue(success_d.called)
        self.assertEqual(len(logger.mock_calls), 0)

        logger.reset_mock()
        err_d = _raiseorreturn(ValueError('Failure!'))
        self.assertTrue(err_d.called)
        self.assertEqual(len(logger.mock_calls), 2)
        self.assertEqual(logger.mock_calls[0], mock.call.log(logging.DEBUG, 'Unhandled error:'))
        self.assertRegex(logger.mock_calls[1][1][1].replace(os.linesep, ' '), r'^Traceback \(most recent call last\):\s.*ValueError: Failure!$')

    def test_logerrbackdl(self):
        logger = mock.Mock()
        d0 = t_defer.maybeDeferred(self._raiseorreturn)
        d1 = t_defer.maybeDeferred(self._raiseorreturn, ValueError('d1 failed!'))
        d2 = t_defer.maybeDeferred(self._raiseorreturn, ValueError('d2 failed!'))
        dl = t_defer.DeferredList(( d0, d1, d2 ))

        msg = 'Unhandled error in dl:'
        dl.addCallback(logerrbackdl, log_lvl=logging.INFO, logger=logger, msg=msg, handled=( Exception, ), suppress_msg_on_handled=False)
        self.assertTrue(dl.called)
        self.assertEqual(len(logger.mock_calls), 4)
        self.assertEqual(logger.mock_calls[0], mock.call.log(logging.INFO, msg))
        self.assertRegex(logger.mock_calls[1][1][1].replace(os.linesep, ' '), r'^Traceback \(most recent call last\):\s.*ValueError: d1 failed!$')
        self.assertEqual(logger.mock_calls[2], mock.call.log(logging.INFO, msg))
        self.assertRegex(logger.mock_calls[3][1][1].replace(os.linesep, ' '), r'^Traceback \(most recent call last\):\s.*ValueError: d2 failed!$')

        d1.addErrback(lambda _res: None) # silence the unhandled error
        d2.addErrback(lambda _res: None) # silence the unhandled error

    #---- Private methods ------------------------------------------------

    def _raiseorreturn(self, err=None):
        if err is not None:
            raise err # pylint: disable=raising-bad-type

        return 'Success!'

#---- Initialization -----------------------------------------------------

if __name__ == '__main__':
    from unittest import main
    main()
