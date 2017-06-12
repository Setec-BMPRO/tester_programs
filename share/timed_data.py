#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data Dictionary with timeout.

Maintains a Dictionary of data, and implements a timeout such that some time
after the last data write, the dictionary is cleared.

"""

import threading
import copy
import logging
from .ticker import RepeatTimer


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
            del self.data[name]
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
