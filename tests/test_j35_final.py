#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Final Test program."""

import unittest
from unittest.mock import patch
import logging
from pydispatch import dispatcher
import tester
from . import logging_setup
from programs import j35

_PROG_NAME = 'J35 Final'
_PROG_CLASS = j35.Final
_PROG_LIMIT = j35.FIN_LIMIT


class J35_Final_TestCase(unittest.TestCase):

    """J35 Final program test suite."""

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

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self._result = result

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self._test_program.sensors
        for sensor in sen.vloads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self._test_program.sensors
        # Tuples of sensor data
        self._sensor_data = {
            'PowerUp': ((sen.photo, (0.0, 12.0)), ),
            'OCP': ((sen.vload1, (12.7, ) * 10 + (11.0, ), ), ),
            }
        # Callables
        self._callables = {
            'PowerUp': (self._dmm_loads, 12.7),
            'Load': (self._dmm_loads, 12.7),
            }
        self._tester.test(('UUT1', ))
        self.assertEqual('P', self._result.code)        # Test Result
        self.assertEqual(31, len(self._result.readings)) # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'Load', 'OCP'],
            self._steps)
