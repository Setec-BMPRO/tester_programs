#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35C Final Test program."""

import unittest
from unittest.mock import patch
import logging
import tester
from . import logging_setup
from .data_feed import DataFeeder
from programs import j35

_PROG_CLASS = j35.Final
_PROG_LIMIT = j35.FIN_LIMIT_C


class J35Final(unittest.TestCase):

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
        cls.tester = tester.Tester(
            'MockATE', (('ProgName', _PROG_CLASS, _PROG_LIMIT), ), fifo=True)
        cls.program = tester.TestProgram(
            'ProgName', per_panel=1, parameter=None, test_limits=[])
        cls.feeder = DataFeeder()

    def setUp(self):
        """Per-Test setup."""
        self.tester.open(self.program)
        self.test_program = self.tester.runner.program

    def tearDown(self):
        """Per-Test tear down."""
        self.tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        cls.patcher.stop()
        cls.feeder.stop()
        cls.tester.stop()

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen.vloads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'PowerUp': ((sen.photo, (0.0, 12.0)), ),
                'OCP': ((sen.vload1, (12.7, ) * 10 + (11.0, ), ), ),
                },
            DataFeeder.key_call: {      # Callables
                'PowerUp': (self._dmm_loads, 12.7),
                'Load': (self._dmm_loads, 12.7),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(31, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(['PowerUp', 'Load', 'OCP'], self.feeder.steps)
