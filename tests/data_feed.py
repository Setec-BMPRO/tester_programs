#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Data feeder version of a Tester for Test programs during unittest.

Subscribe to Tester signals.
Feed FIFO data to Test programs.
Record the test result.

"""

import unittest
from unittest.mock import patch
import logging
from . import logging_setup
from pydispatch import dispatcher
import tester


class UnitTester(tester.Tester):

    """Tester with data feeder functionality."""

    # Dictionary keys into data given to ut_load() method
    key_sen = 'Sen'
    key_call = 'Call'
    key_con = 'Con'
    key_con_np = 'ConNP'
    key_ext = 'Ext'

    def __init__(self, prog_class, parameter):
        """Initalise the data feeder."""
        # Create a 'real' Tester instance
        super().__init__('MockATE', {repr(prog_class): prog_class}, fifo=True)
        self.ut_program = tester.TestProgram(
            repr(prog_class), per_panel=1, parameter=parameter, test_limits=[])
        self.ut_result = None
        self.ut_steps = []
        self.ut_data = None
        self.ut_fifo_pusher = None
        self.ut_console_puts = None
        self.extra_puts = None
        dispatcher.connect(     # Subscribe to the TestStep signals
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.connect(     # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)

    def open(self):
        """Open a program, by using our pre-built one."""
        super().open(self.ut_program)

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
        super().stop()

    def ut_load(self, data, fifo_pusher, console_puts=None, extra_puts=None):
        """Per-Test data load.

        @param data Dictionary of FIFO data
        @param fifo_pusher Callable to push FIFO data into sensors
        @param console_puts Callable to push console data

        """
        self.ut_data = data
        self.ut_fifo_pusher = fifo_pusher
        self.ut_console_puts = console_puts
        self.ut_extra_puts = extra_puts
        self.ut_steps.clear()
        self.ut_result = None

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs['name']
        self.ut_steps.append(stepname)
        self._load_sensors(stepname)
        self._load_callables(stepname)
        self._load_console(stepname)
        self._load_console_np(stepname)
        self._load_extra(stepname)

    def _load_sensors(self, stepname):
        """Sensor FIFOs."""
        try:
            dat = self.ut_data[self.key_sen][stepname]
            self.ut_fifo_pusher(dat)
        except KeyError:
            pass

    def _load_callables(self, stepname):
        """Callables."""
        try:
            dat, val = self.ut_data[self.key_call][stepname]
            dat(val)
        except KeyError:
            pass

    def _load_console(self, stepname):
        """Console strings, or None to add a flush stopper."""
        try:
            dat = self.ut_data[self.key_con][stepname]
            for msg in dat:
                if msg is None:
                    self.ut_console_puts('', postflush=1)
                else:
                    self.ut_console_puts(msg, addprompt=True)
        except KeyError:
            pass

    def _load_console_np(self, stepname):
        """Console strings with addprompt=False."""
        try:
            dat = self.ut_data[self.key_con_np][stepname]
            for msg in dat:
                self.ut_console_puts(msg, addprompt=False)
        except KeyError:
            pass

    def _load_extra(self, stepname):
        """Extra strings."""
        try:
            dat = self.ut_data[self.key_ext][stepname]
            for msg in dat:
                self.ut_extra_puts(msg, addprompt=True)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self.ut_result = result


class ProgramTestCase(unittest.TestCase):

    """Product test program wrapper."""

    debug = False
    parameter = None
    _logger_names = ('tester', 'share', 'programs')

    @classmethod
    def setUpClass(cls):
        """Per-Class setup. Startup logging."""
        logging_setup()
        # Set lower level logging level
        for name in cls._logger_names:
            log = logging.getLogger(name)
            log.setLevel(logging.DEBUG if cls.debug else logging.INFO)
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        cls.tester = UnitTester(cls.prog_class, cls.parameter)

    def setUp(self):
        """Per-Test setup."""
        self.tester.open()
        self.test_program = self.tester.runner.program

    def tearDown(self):
        """Per-Test tear down."""
        self.tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        # Reset lower level logging level
        for name in cls._logger_names:
            log = logging.getLogger(name)
            log.setLevel(logging.INFO)
        cls.patcher.stop()
        cls.tester.stop()
