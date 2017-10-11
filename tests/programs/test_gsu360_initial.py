#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GSU360-1TA Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import gsu360


class GSU3601TAInitial(ProgramTestCase):

    """GSU360-1TA Initial program test suite."""

    prog_class = gsu360.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock': (
                    (sen['Lock'], 10.0),
                    ),
                'PowerUp': (
                    (sen['ACin'], 92.0), (sen['PFC'], 400.0),
                    (sen['PriCtl'], 13.0), (sen['PriVref'], 7.4),
                    (sen['o24V'], 24.0), (sen['Fan12V'], 12.0),
                    (sen['SecCtl'], 24.0), (sen['SecVref'], 2.5),
                    ),
                'FullLoad': (
                    (sen['o24V'], 24.0),
                    ),
                'OCP': (
                    (sen['o24V'], (24.0, ) * 15 + (23.0, ), ),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(11, len(result.readings))
        self.assertEqual(
            ['FixtureLock', 'PowerUp', 'FullLoad', 'OCP'],
            self.tester.ut_steps)
