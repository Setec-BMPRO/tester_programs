#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Data feeder version of a Tester for Test programs during unittest.

Subscribe to Tester signals.
Feed FIFO data to Test programs.
Record the test result.

"""

import logging
import queue
import unittest
from unittest.mock import Mock, patch

import tester
from pydispatch import dispatcher

from . import logging_setup


class UnitTester(tester.Tester):

    """Tester with data feeder functionality."""

    # Dictionary keys into data given to ut_load() method
    key_sen = 'Sen'
    key_call = 'Call'

    def __init__(self, prog_class, per_panel, parameter):
        """Initalise the data feeder."""
        # Create a Tester instance
        super().__init__('MockATE', {repr(prog_class): prog_class})
        self.ut_program = tester.TestProgram(
            repr(prog_class), per_panel=per_panel, parameter=parameter)
        self.ut_result = []
        self.ut_steps = []
        self.ut_data = None
        self.ut_sensor_storer = None
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
        super().open(self.ut_program, uut=None)

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

    def ut_load(self, data, sensor_storer):
        """Per-Test data load.

        @param data Dictionary of FIFO data
        @param sensor_storer Callable to push FIFO data into sensors
        @param console_puts Callable to push console data

        """
        self.ut_data = data
        self.ut_sensor_storer = sensor_storer
        self.ut_steps.clear()
        self.ut_result.clear()

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs['name']
        self.ut_steps.append(stepname)
        self._load_sensors(stepname)
        self._load_callables(stepname)

    def _load_sensors(self, stepname):
        """Sensor FIFOs."""
        try:
            dat = self.ut_data[self.key_sen][stepname]
            self.ut_sensor_storer(dat)
        except KeyError:
            pass

    def _load_callables(self, stepname):
        """Callables."""
        try:
            dat, val = self.ut_data[self.key_call][stepname]
            dat(val)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        self.ut_result.append(kwargs['result'])


class ProgramTestCase(unittest.TestCase):

    """Product test program wrapper."""

    debug = False
    parameter = None
    _logger_names = ('tester', 'share', 'programs')
    per_panel = 1

    @classmethod
    def setUpClass(cls):
        """Per-Class setup."""
        logging_setup()
        # Set lower level logging level
        for name in cls._logger_names:
            log = logging.getLogger(name)
            log.setLevel(logging.DEBUG if cls.debug else logging.INFO)
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        # Create the tester instance
        cls.tester = UnitTester(cls.prog_class, cls.per_panel, cls.parameter)
        cls.tester.start()

    def setUp(self):
        """Per-Test setup."""
        # Patch queue.get to speed up open() by removing the UI ping delays
        myq = Mock(name='MyQueue')
        myq.get.side_effect = queue.Empty
        patcher = patch('queue.Queue', return_value=myq)
        patcher.start()
        self.tester.open()
        patcher.stop()
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
