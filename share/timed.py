#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""General purpose Timer classes."""

import copy
import threading

import attr


# TODO: Remove this when attrs gt validator is available
def _gt_zero(instance, _, value):
    """Pre attrs 21.3 'gt' validator."""
    if value <= 0:
        raise ValueError("Value must be greater than zero")


@attr.s
class BackgroundTimer:

    """Generic second timer with a 'done' property."""

    # interval = attr.ib(converter=float, validator=attr.validators.gt(0.0))
    interval = attr.ib(converter=float, validator=_gt_zero)
    _stop = attr.ib(init=False, factory=threading.Event)
    _worker = attr.ib(init=False, default=None)

    def start(self):
        """Start timer."""
        self.stop()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def _run(self):
        """Run using the timeout of Event.wait."""
        self._stop.wait(self.interval)
        self._stop.set()

    @property
    def done(self):
        """Timer done status.

        @return True if timer has completed

        """
        return self._stop.is_set()

    def wait(self, timeout=None):
        """Wait for timer.

        @param timeout Maximum number of seconds to wait
        @return True if timer has completed

        """
        return self._stop.wait(timeout)

    def stop(self):
        """Stop timer."""
        if self._worker:
            self._stop.set()
            self._worker.join()
            self._worker = None
        self._stop.clear()


@attr.s
class RepeatTimer:

    """Repeatedly call a function at a regular interval."""

    # interval = attr.ib(converter=float, validator=attr.validators.gt(0.0))
    interval = attr.ib(converter=float, validator=_gt_zero)
    function = attr.ib(validator=attr.validators.is_callable())
    _stop = attr.ib(init=False, factory=threading.Event)
    _worker = attr.ib(init=False, default=None)

    def start(self):
        """Start timer."""
        self.stop()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def _run(self):
        """Run using the timeout of Event.wait."""
        while not self._stop.is_set():
            self._stop.wait(self.interval)
            if not self._stop.is_set():
                self.function()

    def stop(self):
        """Stop timer."""
        if self._worker:
            self._stop.set()
            self._worker.join()
            self._worker = None
        self._stop.clear()


@attr.s
class TimedStore:

    """Dictionary with timeout.

    Manage a stored dictionary of data.
    Implement a timeout so that the data clears some time after the last
    value has been written.
    Use a RLock to make the data store thread safe.

    """

    default = attr.ib(validator=attr.validators.instance_of(dict))
    # timeout = attr.ib(converter=float, validator=attr.validators.gt(0.0))
    timeout = attr.ib(converter=float, validator=_gt_zero)
    data = attr.ib(init=False, factory=dict)
    tick_interval = attr.ib(init=False, default=0.5)
    _timer = attr.ib(init=False, default=None)
    _lock = attr.ib(init=False, factory=threading.RLock)
    _ticks_total = attr.ib(init=False, default=0)
    _ticks_left = attr.ib(init=False, default=0)

    def _tick_handler(self):
        """Reset data dictionary if the timeout has expired."""
        with self._lock:
            if self._ticks_left > -1:  # After reset, stay at -1
                self._ticks_left -= 1
            if not self._ticks_left:
                self.reset()

    def start(self):
        """Start running."""
        self.reset()
        self._ticks_total = round(self.timeout / self.tick_interval)
        self._ticks_left = self._ticks_total
        self._timer = RepeatTimer(self.tick_interval, self._tick_handler)
        self._timer.start()

    def stop(self):
        """Stop running."""
        self._timer.stop()
        self._timer = None

    def reset(self):
        """Reset the saved data state by copying from the default."""
        with self._lock:
            self.data = copy.deepcopy(self.default)

    def __getitem__(self, name):
        """Get an item's value.

        @param name Dictionary key
        @return Value.

        """
        with self._lock:
            return self.data[name]

    def __setitem__(self, name, value):
        """Set a value and reset the data lifetime timer.

        @param name Dictionary key
        @param value Dictionary value to store

        """
        with self._lock:
            self.data[name] = value
            self._ticks_left = self._ticks_total

    def __delitem__(self, name):
        """Delete an item and reset the data lifetime timer.

        @param name Dictionary key

        """
        with self._lock:
            del self.data[name]
            self._ticks_left = self._ticks_total

    def __len__(self):
        """Return length of the data dictionary."""
        with self._lock:
            return len(self.data)