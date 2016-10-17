#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVVIEW Initial Test program."""

import unittest
from unittest.mock import patch
import logging
from pydispatch import dispatcher
import tester
from . import logging_setup
from programs import rvview

_PROG_NAME = 'RVVIEW Initial'
_PROG_CLASS = rvview.Initial
_PROG_LIMIT = rvview.INI_LIMIT


class RVVIEW_Initial_TestCase(unittest.TestCase):

    """RVVIEW Initial program test suite."""

    @classmethod
    def setUpClass(cls):
        """Per-Class setup. Startup logging."""
        logging_setup()
        # Set lower level logging
        log = logging.getLogger('tester')
        log.setLevel(logging.INFO)
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        cls._tester = tester.Tester(
            'MockATE', ((_PROG_NAME, _PROG_CLASS, _PROG_LIMIT), ), fifo=True)
        cls._program = tester.TestProgram(
            _PROG_NAME, per_panel=1, parameter=None, test_limits=[])

    def setUp(self):
        """Per-Test setup."""
        self._tester.open(self._program)
        self._test_program = self._tester.runner.program
        self._sensor_data = {}
        self._callables = {}
        self._console_data = {}
        self._console_np_data = {}
        self._result = None
        self._steps = []
        dispatcher.connect(     # Subscribe to the TestStep signals
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.connect(     # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)

    def tearDown(self):
        """Per-Test tear down."""
        dispatcher.disconnect(
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.disconnect(
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)
        self._tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        cls.patcher.stop()

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs['name']
        self._steps.append(stepname)
        dev = self._test_program.logdev
        try:    # Sensor data
            data = self._sensor_data[stepname]
            self._test_program.fifo_push(data)
        except KeyError:
            pass
        try:    # Callables
            data, value = self._callables[stepname]
            data(value)
        except KeyError:
            pass
        try:    # Console strings
            data = self._console_data[stepname]
            for msg in data:
                dev.rvview_puts(msg)
        except KeyError:
            pass
        try:    # Console strings with addprompt=False
            data = self._console_np_data[stepname]
            for msg in data:
                dev.rvview_puts(msg, addprompt=False)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self._result = result

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self._test_program.sensors
        # Tuples of sensor data
        self._sensor_data = {
            'PowerUp':
                ((sen.oSnEntry, ('A1626010123', )), (sen.oVin, 7.5),
                 (sen.o3V3, 3.3), ),
            'Display':
                ((sen.oYesNoOn, True), (sen.oYesNoOff, True),
                 (sen.oBkLght, (3.0, 0.0)), ),
            }
        # Callables
        self._callables = {}
        # Tuples of console strings
        self._console_data = {
            'Initialise':
                ('Banner1\r\nBanner2', ) +
                ('', ) + ('success', ) * 2 + ('', ) +
                ('Banner1\r\nBanner2', ) +
                (rvview.initial.limit.BIN_VERSION, ),
            'Display': ('0x10000000', '', '0x10000000', '', ),
            'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
            }
        # Tuples of strings with addprompt=False
        self._console_np_data = {
            'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
            }
        self._tester.test(('UUT1', ))
        self.assertEqual('P', self._result.code)            # Test Result
        self.assertEqual(10, len(self._result.readings))    # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'Initialise', 'Display', 'CanBus'],
            self._steps)
