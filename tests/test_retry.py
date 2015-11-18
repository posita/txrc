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
import sys
from twisted.internet import (
    defer as t_defer,
    task as t_task,
)
from twisted.python import failure as t_failure
from twisted.trial import unittest as t_unittest

from txrc.retry import (
    RetryingCaller,
    TimeoutError,
    calltimeout,
    calltimeoutexc,
)
import tests # pylint: disable=unused-import
from tests.symmetries import mock

#---- Constants ----------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

#---- Classes ------------------------------------------------------------

#=========================================================================
class CallTimeoutTestCase(t_unittest.TestCase):

    longMessage = True

    #---- Public hooks ---------------------------------------------------

    def setUp(self):
        super().setUp()
        self._clock = t_task.Clock()
        self._state = CallTimeoutTestCase._State(self._clock)

    def tearDown(self):
        super().tearDown()

    def test_deferred_cancel(self):
        delay = 2
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.deferredcall, call_val, sys.maxsize >> 1)
        self._clock.advance(0)
        d.cancel()
        self._clock.advance(1)
        self. assertFailure(d, t_defer.CancelledError)
        self.assertFalse(self._state.fired)
        self.assertEqual(len(self._clock.getDelayedCalls()), 0)
        d.addErrback(lambda _res: None) # silence the unhandled error

    def test_deferred_delayed(self):
        delay = 2
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.deferredcall, call_val)
        self._clock.advance(0)
        self.assertFalse(hasattr(d, 'result'))

        for _ in range(delay + 1):
            self._clock.advance(1)
            self.assertEqual(d.result, call_val)
            self.assertTrue(self._state.fired)

    def test_deferred_immediate(self):
        delay = 0
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.deferredcall, call_val)
        self._clock.advance(0)
        self. assertFailure(d, TimeoutError)
        self.assertFalse(self._state.fired)
        self._clock.advance(2)
        self. assertFailure(d, TimeoutError)
        self.assertFalse(self._state.fired)
        self.assertFalse(self._clock.getDelayedCalls())
        d.addErrback(lambda _res: None) # silence the unhandled error

    def test_deferred_immediate_exc(self):
        delay = 0
        call_val = 'done'
        d = calltimeoutexc(self._clock, delay, self._state.deferredcall, ValueError, call_val)
        self._clock.advance(0)
        self.assertIsInstance(d.result.value, ValueError)
        self.assertFalse(self._state.fired)
        self.assertFalse(self._clock.getDelayedCalls())
        d.addErrback(lambda _res: None) # silence the unhandled error

    def test_deferred_negative_timeout(self):
        delay = -1
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.deferredcall, call_val, 9)
        self._clock.advance(10)
        self.assertEqual(d.result, call_val)
        self.assertTrue(self._state.fired)
        self.assertFalse(self._clock.getDelayedCalls())

    def test_nondeferred_delayed(self):
        delay = 2
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.nondeferredcall, call_val)
        self._clock.advance(0)
        self.assertEqual(d.result, call_val)
        self.assertTrue(self._state.fired)

        for _ in range(delay + 1):
            self._clock.advance(1)
            self.assertEqual(d.result, call_val)
            self.assertTrue(self._state.fired)

        self.assertFalse(self._clock.getDelayedCalls())

    def test_nondeferred_immediate(self):
        delay = 0
        call_val = 'done'
        d = calltimeout(self._clock, delay, self._state.nondeferredcall, call_val)
        self._clock.advance(0)
        self.assertEqual(d.result, call_val)
        self.assertTrue(self._state.fired)
        self.assertFalse(self._clock.getDelayedCalls())

    #---- Private inner classes ------------------------------------------

    class _State(object):

        #---- Constructor ------------------------------------------------

        def __init__(self, clock):
            self.clock = clock
            self.fired = False

        #---- Public methods ---------------------------------------------

        def deferredcall(self, val, wait_seconds=1):
            d = t_task.deferLater(self.clock, wait_seconds, self.nondeferredcall, val)

            return d

        def nondeferredcall(self, val):
            self.fired = True

            return val

#=========================================================================
class RetryingCallerTestCase(t_unittest.TestCase):

    longMessage = True

    #---- Public hooks ---------------------------------------------------

    def setUp(self):
        super().setUp()
        self._clock = t_task.Clock()

    def tearDown(self):
        super().tearDown()
        del self._clock

    def test_first_error(self):
        err_msg = 'Weee!'

        def _none(*_, **__): # pylint: disable=unused-argument
            return

        def _raise(*_, **__): # pylint: disable=unused-argument
            raise RuntimeError(err_msg)

        def _call():
            dl = t_defer.DeferredList(( t_defer.maybeDeferred(_none), t_defer.maybeDeferred(_raise) ), fireOnOneErrback=True, consumeErrors=True)

            return dl

        retrying_caller = RetryingCaller(0, reactor=self._clock)
        d = retrying_caller.retry(_call)
        self._clock.advance(0)
        self. assertFailure(d, RuntimeError)
        self.assertEqual(d.result.args, ( err_msg, ))
        d.addErrback(lambda _res: None) # silence the unhandled error

    def test_retry(self):
        retries = 5
        retrier = RetryingCaller(retries, reactor=self._clock)

        ret_vals_0 = tuple(( ValueError('call_0 attempt {}'.format(i)) for i in range(retries - 1) )) + ( 'success_0', )
        call_0 = mock.Mock(side_effect=ret_vals_0)
        d_0 = retrier.retry(call_0)

        ret_vals_1 = tuple(( ValueError('call_1 attempt {}'.format(i)) for i in range(retries) )) + ( 'success_1', )
        call_1 = mock.Mock(side_effect=ret_vals_1)
        d_1 = retrier.retry(call_1)

        ret_vals_2 = tuple(( ValueError('call_2 attempt {}'.format(i)) for i in range(retries + 1) )) + ( 'success_2', )
        call_2 = mock.Mock(side_effect=ret_vals_2)
        d_2 = retrier.retry(call_2)

        dl = t_defer.DeferredList(( d_0, d_1, d_2 ), consumeErrors=True)
        self._clock.advance(0)
        self._clock.pump(RetryingCaller.DoublingBackoffGeneratorFactoryMixin._basegenerator(retries + 1)) # pylint: disable=protected-access

        self.assertTrue(d_0.called)
        self.assertTrue(d_1.called)
        self.assertTrue(d_2.called)
        self.assertTrue(dl.called)

        success_0, ret_val_0 = dl.result[0]
        self.assertTrue(success_0)
        self.assertEqual(ret_val_0, 'success_0')

        expected_0 = [ (), ] * len(ret_vals_0)
        self.assertEqual(call_0.call_args_list, expected_0)

        success_1, ret_val_1 = dl.result[1]
        self.assertTrue(success_1)
        self.assertEqual(ret_val_1, 'success_1')

        expected_1 = [ (), ] * len(ret_vals_1)
        self.assertEqual(call_1.call_args_list, expected_1)

        success_2, ret_val_2 = dl.result[2]
        self.assertFalse(success_2)
        self.assertIsInstance(ret_val_2, t_failure.Failure)
        self.assertIsNotNone(ret_val_2.check(ValueError))
        error_2 = ret_val_2.value
        self.assertEqual(error_2.args, ( 'call_2 attempt {}'.format(retries), ))

        expected_2 = [ (), ] * (len(ret_vals_2) - 1)
        self.assertEqual(call_2.call_args_list, expected_2)

    def test_retry_cancel(self):
        retries = 5
        retrier = RetryingCaller(retries, reactor=self._clock)

        ret_vals = tuple(( ValueError('call attempt {}'.format(i)) for i in range(retries) )) + ( 'success', )
        call = mock.Mock(side_effect=ret_vals)
        d = retrier.retry(call)
        self._clock.advance(0)
        d.cancel()
        self._clock.pump(RetryingCaller.DoublingBackoffGeneratorFactoryMixin._basegenerator(retries + 1)) # pylint: disable=protected-access

        expected = [ (), ]
        self.assertEqual(call.call_args_list, expected)
        self.assertFailure(d, t_defer.CancelledError)
        d.addErrback(lambda _res: None) # silence the unhandled error

    def test_retry_on(self):
        errors = ( TimeoutError, TimeoutError, t_defer.CancelledError )

        retries = len(errors) + 1
        failure_inspector = RetryingCaller.RetryOnFailureInspectorMixin()
        failure_inspector.retry_on = ( TimeoutError, )
        retrier = RetryingCaller(retries, failure_inspector_factory=failure_inspector, reactor=self._clock)

        error_raiser = mock.Mock(side_effect=errors)
        d = retrier.retry(error_raiser, -273)
        self._clock.advance(0)
        self._clock.pump(RetryingCaller.DoublingBackoffGeneratorFactoryMixin._basegenerator(retries)) # pylint: disable=protected-access

        expected = [
            ( ( -273, ), ),
            ( ( -273, ), ),
            ( ( -273, ), ),
        ]

        self.assertTrue(d.called)
        self.assertEqual(error_raiser.call_args_list, expected)
        self.assertFailure(d, t_defer.CancelledError)
        d.addErrback(lambda _res: None) # silence the unhandled error

#---- Initialization -----------------------------------------------------

if __name__ == '__main__':
    from unittest import main
    main()
