#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Data feeder version of a Tester for Test programs during unittest.

Subscribe to Tester signals.
Feed FIFO data to Test programs.
Record the test result.

"""

import unittest
from unittest.mock import MagicMock, PropertyMock, patch
import queue
import logging
from . import logging_setup
from pydispatch import dispatcher
import tester


class UnitTester(tester.Tester):

    """Tester with data feeder functionality."""

    # Dictionary keys into data given to ut_load() method
    key_sen = 'Sen'
    key_call = 'Call'

    def __init__(self, prog_class, parameter):
        """Initalise the data feeder."""
        # Create a Tester instance
        super().__init__('MockATE', {repr(prog_class): prog_class})
        self.ut_program = tester.TestProgram(
            repr(prog_class), per_panel=1, parameter=parameter)
        self.ut_result = None
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
        self.ut_result = None

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
        result = kwargs['result']
        self.ut_result = result


class MockATE(dict):

    """A Mock ATE."""

    def __init__(self, tester_type):
        """Create Mock ATE."""
        self.tester_type = tester_type
        # Dummy methods
        self.opc = lambda: None
        self.error = lambda: None
        self.close = lambda: None
        # Build a dictionary of Mocks
        storage = {}
        for dev_name in ('GEN', 'ACS', 'DIS', 'PWR', 'SAF'):
            storage[dev_name] = MagicMock(name=dev_name)
        gen = storage['GEN']
        for dev_name in ('DMM', 'DSO'):
            storage[dev_name] = (MagicMock(name=dev_name), gen)
        # Patch a Mock SerialToCAN device
        #   - Property 'ready_can' returns False
        mycan = MagicMock(name='SerialToCan')
        type(mycan).ready_can = PropertyMock(return_value=False)
        storage['_CAN'] = mycan
        storage['CAN'] = (mycan, MagicMock(name='SimSerial'))
        for i in range(1, 8):           # DC Sources 1 - 7
            dev_name = 'DCS{0}'.format(i)
            storage[dev_name] = MagicMock(name=dev_name)
        for i in range(1, 8):           # DC Loads 1 - 7
            dev_name = 'DCL{0}'.format(i)
            storage[dev_name] = MagicMock(name=dev_name)
        for i in range(1, 23):          # Relays 1 - 22
            dev_name = 'RLA{0}'.format(i)
            storage[dev_name] = (gen, i)
        super().__init__(storage)


class ProgramTestCase(unittest.TestCase):

    """Product test program wrapper."""

    debug = False
    parameter = None
    _logger_names = ('tester', 'share', 'programs')

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
        # Patch tester physical instruments
        cls.tst_patcher = patch(
            'tester.devphysical.PhysicalDevices', new=MockATE)
        cls.tst_patcher.start()
        # Create the tester instance
        cls.tester = UnitTester(cls.prog_class, cls.parameter)

    def setUp(self):
        """Per-Test setup."""
        # Patch queue.get to speed up open() by removing the UI ping delays
        myq = MagicMock(name='MyQueue')
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
        cls.tst_patcher.stop()
        cls.tester.stop()
