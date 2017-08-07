#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""Background Timer."""

import threading


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
