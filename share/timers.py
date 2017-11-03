#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""Timer utilities."""

import threading
import copy
import logging


class BackgroundTimer():

    """A timer to keep track of elapsed time in the background."""

    _event = None
    _timer = None

    def __init__(self):
        """Create the timer."""
        self._event = threading.Event()

    def start(self, delay):
        """Start the timer.

        @param delay Delay time in sec to timed_data

        """
        self._event.clear()
        self._timer = threading.Timer(delay, self._event.set)
        self._timer.start()

    @property
    def running(self):
        """Timer status.

        @return True if timer is running

        """
        return self._timer is not None

    def wait(self):
        """Wait for the timer to finish."""
        if self._timer:
            self._event.wait()
            self._timer = None

    def cancel(self):
        """Cancel any running timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None


class RepeatTimer(threading.Thread):

    """Repeat Timer.

    Required Args:
        interval:   Floating point number specifying the number of seconds
                    to wait before executing function
        function:   The function (or callable object) to be executed
    Optional Args:
        iterations: Integer specifying the number of iterations to perform
        args:       List of positional arguments passed to function
        kwargs:     Dictionary of keyword arguments passed to function

    """

#    Copyright (c) 2009 Geoffrey Foster.
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without
#    restriction, including without limitation the rights to use,
#    copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following
#    conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#    OTHER DEALINGS IN THE SOFTWARE.

    def __init__(self, interval, function,
                 iterations=0, name=None,
                 args=None, kwargs=None):
        """Initialise class."""
        super().__init__(name=name)
        self._interval = interval
        self._function = function
        self._iterations = iterations
        self._args = [] if args is None else args
        self._args = {} if kwargs is None else kwargs
        self._myevent = threading.Event()

    def run(self):
        """Start the 'timer' running by using the timeout of Event.wait."""
        count = 0
        while not self._myevent.is_set() and (
                self._iterations <= 0 or count < self._iterations):
            self._myevent.wait(self._interval)
            if not self._myevent.is_set():
                self._function(*self._args, **self._kwargs)
                count += 1

    def cancel(self):
        """Stop the timer."""
        self._myevent.set()


class TimedStore():

    """Dictionary with timeout.

    Manage the stored dictionary of data.
    Implement a timeout so that the data clears some time after the last
    value has been saved.
    Use a Lock to make the data store multithread safe.

    """

    def __init__(self, template, timeout=5.0):
        """Clear data state, and start the data lifetime timer."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.info('Started')
        self._lock = threading.Lock()
        self._template = template
        self.data = {}              # Template
        self._timeout = timeout     # Data lifetime in seconds
        self._timer = 0             # Timer is not running
        self.clear()
        # Create a data timer thread
        self._tick = 0.5              # The tick interval to use for timing
        self._rpt = RepeatTimer(self._tick, self._tick_handler)
        self._rpt.start()

    def clear(self):
        """Clear the saved data state by copying from the template."""
        self._logger.debug('clear data')
        with self._lock:
            self.data = copy.deepcopy(self._template)

    def __getitem__(self, name):
        """Get an item's value.

        @return Item value.

        """
        with self._lock:
            value = self.data[name]
        return value

    def __setitem__(self, name, val):
        """Set an item's value.

        Reset the data lifetime timer

        """
        with self._lock:
            self.data[name] = val
        self._timer = self._timeout / self._tick

    def __delitem__(self, name):
        """Delete an item.

        Reset the data lifetime timer

        """
        with self._lock:
            self.data.pop(name)
        self._timer = self._timeout / self._tick

    def __len__(self):
        """Return length of the data store."""
        with self._lock:
            length = len(self.data)
        return length

    def _tick_handler(self):
        """Handle a data lifetime timer tick.

        Decrement the counter, and when it reaches zero, clear the saved data.

        """
        if self._timer > -1:     # don't let it go below -1
            self._timer -= 1
        if self._timer == 0:
            self.clear()

    def cancel(self):
        """Stop the timer."""
        self._logger.debug('cancel')
        self._rpt.cancel()
