# -*- encoding: utf-8; grammar-ext: py; mode: python; test-case-name: test.test_retry -*-

# ========================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not expressly
waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before
viewing or using this software in any capacity.

Portions of this code are adapted from `this blog post by Terry Jones
<http://blogs.fluidinfo.com/terry/2009/11/12/twisted-code-for-retrying-function-calls/>`__.
Per its author's terms, its use herein is permitted under the
`CC0 1.0 License`_.

Portions of this code are adapted from `this Gist
<https://gist.github.com/theduderog/735556>`__. Per its authors' terms,
its use herein is permitted under the `CC0 1.0 License`_.

.. _`CC0 1.0 License`: https://creativecommons.org/publicdomain/zero/1.0/
"""
# ========================================================================

from __future__ import (
    absolute_import, division, print_function, unicode_literals,
)
from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import functools
import logging
from twisted.internet import defer as t_defer
from twisted.internet import task as t_task
from zope import interface

from .logging import (
    SILENT,
    formattraceback,
)

# ---- Constants ---------------------------------------------------------

__all__ = (
    'DeferredTimeoutError',
    'RetryingCaller',
    'calltimeout',
    'calltimeoutexc',
    'deferredtimeout',
)

_LOGGER = logging.getLogger(__name__)

# ---- Exceptions --------------------------------------------------------

# ========================================================================
class DeferredTimeoutError(Exception):
    ""

    # ---- Public properties ---------------------------------------------

    target_d = None

# ---- Interfaces --------------------------------------------------------

# ========================================================================
class IBackoffGeneratorFactory(interface.Interface):  # pylint: disable=inherit-non-class
    """
    Factory for creating a backoff generator for use with a
    :class:`RetryingCaller`.
    """
    # pylint: disable=no-method-argument,no-self-argument,useless-suppression

    # ---- Hooks ---------------------------------------------------------

    def buildbackoffgenerator(retries):
        """
        Factory method.

        :param Integral retries: the number of retries the backoff
            generator should attempt before finishing; usually this is
            passed from a :class:`RetryingCaller`

        :returns: a generator yielding at most ``retries`` delays
            (measured in seconds)
        """

# ========================================================================
class IFailureInspector(interface.Interface):  # pylint: disable=inherit-non-class
    """
    Inspects a :class:`twisted.python.failure.Failure` and decides whether
    or not the call the generated it should be retried.
    """
    # pylint: disable=no-method-argument,no-self-argument,useless-suppression

    # ---- Hooks ---------------------------------------------------------

    def shouldretry(failure):
        """
        Called by a :class:`RetryingCaller` after each call failure.

        :param failure: the failure raised from the underlying call

        :type failure: :class:`twisted.python.failure.Failure`

        :returns: a tuple in the format ``( Failure, bool )``, where the
            first item is the :class:`~twisted.python.failure.Failure`
            that should be raised if the number of retries has been
            exhausted, or if the second item is :constant:`True`
        """

# ========================================================================
class IFailureInspectorFactory(interface.Interface):  # pylint: disable=inherit-non-class
    """
    Factory for creating a :class:`FailureInspector` for use with a
    :class:`RetryingCaller`.
    """
    # pylint: disable=no-method-argument,no-self-argument,useless-suppression

    # ---- Hooks ---------------------------------------------------------

    def buildfailureinspector():
        """
        Factory method.

        :returns: a :class:`IFailureInspector` provider
        """

# ---- Classes -----------------------------------------------------------

# ========================================================================
class RetryingCaller(object):
    """
    Partial with the ability to retry the call on failure. Adapted from
    `Terry Jones's proposal
    <http://blogs.fluidinfo.com/terry/2009/11/12/twisted-code-for-retrying-function-calls/>`__.

    :param Integral retries: the number of times to retry (0 means call
        once with no retries)

    :param backoff_generator_factory: the factory used to generate the
        backoff delays between each retry attempt

    :type backoff_generator_factory: :class:`IBackoffGeneratorFactory`

    :param failure_inspector_factory: the factory used to generate the
        failure inspector used to determin if a retry should be attempted

    :type failure_inspector_factory: :class:`IFactoryInspectorFactory`

    :param reactor: the reactor to use; if :constant:`None`, then
        `twisted.internet.reactor` is used

    :type reactor: :class:`twisted.internet.interfaces.IReactorTime`
    """

    # ---- Public inner classes ------------------------------------------

    @interface.implementer(IBackoffGeneratorFactory)
    class DoublingBackoffGeneratorFactoryMixin(object):
        """
        Implements the default :class:`IBackoffGeneratorFactory` provider
        for a :class:`RetryingCaller` as a mix-in.
        """

        # ---- Public hooks ----------------------------------------------

        def buildbackoffgenerator(self, retries):
            """
            A :attr:`IBackoffGeneratorFactory:buildbackoffgenerator`
            provider that yields delays that start with 0.25 and double
            for each subsequent attempt up to ``retries`` times.
            """
            for delay in self._basegenerator(retries):
                yield delay

        # ---- Private static methods ------------------------------------

        @staticmethod
        def _basegenerator(retries):
            return ( min((1 << e) / 4, 32.0) for e in range(retries) )

    @interface.implementer(IFailureInspectorFactory, IFailureInspector)
    class HaltOnFailureInspectorMixin(object):
        """
        Implements the default :class:`IFailureInspector` provider for a
        :class:`RetryingCaller` as a mix-in.
        """

        # ---- Public constants ------------------------------------------

        halt_on = ( t_defer.CancelledError, )

        # ---- Public hooks ----------------------------------------------

        def buildfailureinspector(self):
            return self

        def shouldretry(self, failure):
            """
            A :attr:`IFailureInspector.shouldretry` provider that passes
            through the underlying failure, which is usually ``failure``,
            unless it is a :class:`twisted.internet.defer.FirstError`,
            in which case the ``subFailure`` attribute of
            :attr:`twisted.internet.defer.Failure.value` will be passed
            through. This method signals that the call should be retried
            unless the underlying
            :attr:`twisted.internet.defer.Failure.value` can be found in
            ``self.halt_on``.
            """
            if isinstance(failure.value, t_defer.FirstError):
                failure = failure.value.subFailure

            halt_now = failure.check(*self.halt_on) is not None

            return failure, halt_now

    @interface.implementer(IFailureInspectorFactory, IFailureInspector)
    class RetryOnFailureInspectorMixin(object):
        """
        Implements the default :class:`IFailureInspector` provider for a
        :class:`RetryingCaller` as a mix-in.
        """

        # ---- Public constants ------------------------------------------

        retry_on = ( DeferredTimeoutError, )

        # ---- Public hooks ----------------------------------------------

        def buildfailureinspector(self):
            return self

        def shouldretry(self, failure):
            """
            A :attr:`IFailureInspector.shouldretry` provider that passes
            through the underlying failure, which is usually ``failure``,
            unless it is a :class:`twisted.internet.defer.FirstError`,
            in which case the ``subFailure`` attribute of
            :attr:`twisted.internet.defer.Failure.value` will be passed
            through. This method signals that the call should be retried
            if the underlying
            :attr:`twisted.internet.defer.Failure.value` can be found in
            ``self.retry_on``.
            """
            if isinstance(failure.value, t_defer.FirstError):
                failure = failure.value.subFailure

            halt_now = failure.check(*self.retry_on) is None

            return failure, halt_now

    # ---- Private constants ---------------------------------------------

    _DEFAULT_BACKOFF_GENERATOR_FACTORY = DoublingBackoffGeneratorFactoryMixin()
    _DEFAULT_FAILURE_INSPECTOR_FACTORY = HaltOnFailureInspectorMixin()

    # ---- Constructor ---------------------------------------------------

    # ====================================================================
    def __init__(self, retries, backoff_generator_factory=_DEFAULT_BACKOFF_GENERATOR_FACTORY, failure_inspector_factory=_DEFAULT_FAILURE_INSPECTOR_FACTORY, log_lvl=SILENT, logger=_LOGGER, reactor=None):
        self._retries = retries
        self._log_lvl = log_lvl
        self._logger = logger
        self._backoff_generator_factory = backoff_generator_factory
        self._failure_inspector_factory = failure_inspector_factory

        if reactor is None:
            from twisted.internet import reactor

        self._reactor = reactor

    # ---- Public hook methods -------------------------------------------

    # ====================================================================
    def __call__(self, _call):
        """
        Allows a :class:`RetryingCaller` object to be used as a
        decorator:

        .. code-block:: python
            :linenos:

            retry = RetryingCaller(retries=3, ...)
            @retry
            def calltoretry(...):
                ...
        """
        def _retrywrapper(*__args, **__kw):
            return self.retry(_call, *__args, **__kw)

        try:
            _retrywrapper = functools.wraps(_call)(_retrywrapper)
        except AttributeError:
            pass

        return _retrywrapper

    # ---- Public methods ------------------------------------------------

    # ====================================================================
    def retry(self, call, *args, **kw):
        """
        Retries ``call(*args, **kw)`` upon failure.

        :returns: a :class:`twisted.internet.defer.Deferred` for ``call``
            whose errback will be called with the most recent
            :class:`twisted.python.failure.Failure` returned by
            :meth:`FailureInspector.shouldretry` once all retries are
            exhausted
        """
        backoff_gen = self._backoff_generator_factory.buildbackoffgenerator(self._retries)
        failure_inspector = self._failure_inspector_factory.buildfailureinspector()

        def _retry(_failure=None):
            if _failure is not None:
                tested_failure, halt_now = failure_inspector.shouldretry(_failure)

                if not halt_now:
                    try:
                        self._logger.log(self._log_lvl, 'call failed')
                        self._logger.log(self._log_lvl, formattraceback(_failure))
                        delay = next(backoff_gen)
                        self._logger.log(self._log_lvl, 'retrying in %0.3f seconds', delay)
                    except StopIteration:
                        halt_now = True

                if halt_now:
                    return tested_failure
            else:
                delay = 0

            _d = t_task.deferLater(self._reactor, delay, call, *args, **kw)
            _d.addErrback(_retry)

            return _d

        return _retry()

# ---- Functions ---------------------------------------------------------

# ========================================================================
def calltimeout(reactor, timeout, call, *args, **kw):
    """
    Shorthand for ``calltimeoutexc(reactor, timeout, call, None, *args,
    **kw)``.
    """
    return calltimeoutexc(reactor, timeout, call, None, *args, **kw)

# ========================================================================
def calltimeoutexc(reactor, timeout, call, timeout_exc, *args, **kw):
    """
    Calls :func:`twisted.internet.defer.maybeDeferred` on ``call``,
    ``args``, and ``kw`` and passes the result as the ``target_d``
    argument to :func:`deferredtimeout`.

    :param reactor: the reactor to use; if :constant:`None`, then
        `twisted.internet.reactor` is used

    :type reactor: :class:`twisted.internet.interfaces.IReactorTime`

    :param Integral timeout: the timeout in seconds; if ``timeout`` is
        less than zero, there is no timeout

    :param callable call: the callable

    :param Exception timeout_exc: the exception to raise instead of a
        :exc:`DeferredTimeoutError`

    :param args: passed to ``call``

    :param kw: passed to ``call``

    :returns: a :class:`twisted.internet.defer.Deferred` wrapping
        ``call``, ``args``, and ``kw``
    """
    return deferredtimeout(reactor, timeout, t_defer.maybeDeferred(call, *args, **kw), timeout_exc)

# ========================================================================
def deferredtimeout(reactor, timeout, target_d, timeout_exc=None):
    """
    Wraps ``target_d`` with a :class:`twisted.internet.defer.Deferred`
    that calls :meth:`~twisted.internet.defer.Deferred.cancel` on
    ``target_d`` and returns a :class:`twisted.python.failure.Failure`
    with a :exc:`DeferredTimeoutError` after ``timeout`` seconds if
    ``target_d`` hasn't yet fired and ``timeout >= 0``.

    :param reactor: the reactor to use; if :constant:`None`, then
        `twisted.internet.reactor` is used

    :type reactor: :class:`twisted.internet.interfaces.IReactorTime`

    :param Integral timeout: the timeout in seconds; if ``timeout`` is
        less than zero, there is no timeout

    :param target_d: the target

    :type target_d: :class:`twisted.internet.defer.Deferred`

    :param Exception timeout_exc: the exception to raise instead of a
        :exc:`DeferredTimeoutError`

    :returns: a :class:`twisted.internet.defer.Deferred` that wraps
        ``target_d`` if ``timeout >= 0``, otherwise ``target_d``
    """
    if timeout < 0:
        return target_d

    if reactor is None:
        from twisted.internet import reactor

    def _timeout():
        if timeout_exc is None:
            exc = DeferredTimeoutError()
            exc.target_d = target_d
        else:
            exc = timeout_exc

        try:
            raise exc
        except Exception as exc:  # pylint: disable=broad-except
            timeout_d.errback(exc)

        target_d.cancel()

    deadline = reactor.callLater(timeout, _timeout)

    def _canceler(_):
        if deadline.active():
            deadline.cancel()

        target_d.cancel()

    timeout_d = t_defer.Deferred(_canceler)

    def _handler(_passthru):
        if deadline.active():
            deadline.cancel()

        return _passthru

    timeout_d.addBoth(_handler)

    def _suppressalreadycalled(_failure):
        _failure.trap(t_defer.AlreadyCalledError)

    target_d.chainDeferred(timeout_d)
    target_d.addErrback(_suppressalreadycalled)

    return timeout_d
