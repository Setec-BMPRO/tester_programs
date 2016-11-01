#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Data feeder for Test programs during unittest.

Subscribe to Tester signals.
Feed FIFO data to Test programs.
Record the test result.

"""

from pydispatch import dispatcher
import tester


class DataFeeder():

    """DataFeeder class."""

    # Dictionary keys into data given to load() method
    key_sen = 'Sen'
    key_call = 'Call'
    key_con = 'Con'
    key_con_np = 'ConNP'

    def __init__(self):
        """Initalise the data feeder."""
        self.result = None
        self.steps = []
        self.data = None
        self.fifo_pusher = None
        self.console_puts = None
        dispatcher.connect(     # Subscribe to the TestStep signals
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.connect(     # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)

    def stop(self):
        """Release resources."""
        dispatcher.disconnect(
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.disconnect(
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)

    def load(self, data, fifo_pusher, console_puts=None):
        """Per-Test data load.

        @param data Dictionary of FIFO data
        @param fifo_pusher Callable to push FIFO data into sensors
        @param console_puts Callable to push console data

        """
        self.data = data
        self.fifo_pusher = fifo_pusher
        self.console_puts = console_puts
        self.steps.clear()
        self.result = None

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs['name']
        self.steps.append(stepname)
        self._load_sensors(stepname)
        self._load_callables(stepname)
        self._load_console(stepname)
        self._load_console_np(stepname)

    def _load_sensors(self, stepname):
        """Sensor FIFOs."""
        try:
            dat = self.data[self.key_sen][stepname]
            self.fifo_pusher(dat)
        except KeyError:
            pass

    def _load_callables(self, stepname):
        """Callables."""
        try:
            dat, val = self.data[self.key_call][stepname]
            dat(val)
        except KeyError:
            pass

    def _load_console(self, stepname):
        """Console strings."""
        try:
            dat = self.data[self.key_con][stepname]
            for msg in dat:
                self.console_puts(msg)
        except KeyError:
            pass

    def _load_console_np(self, stepname):
        """Console strings with addprompt=False."""
        try:
            dat = self.data[self.key_con_np][stepname]
            for msg in dat:
                self.console_puts(msg, addprompt=False)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self.result = result
