#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copyright (c) 2009 Geoffrey Foster.

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""

import threading


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
