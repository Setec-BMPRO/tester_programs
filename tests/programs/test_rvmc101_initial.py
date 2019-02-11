#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMC101 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmc101


class RVMC101Initial(ProgramTestCase):

    """RVMC101 Initial program test suite."""

    prog_class = rvmc101.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.programmer.ARM')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['vin'], 12.0),
                    ),
                'CanBus': (
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'CanBus'],
            self.tester.ut_steps)
