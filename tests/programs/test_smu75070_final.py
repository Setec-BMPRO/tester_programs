#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SMU750-70 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import smu75070


class SMU750Final(ProgramTestCase):

    """SMU750-70 Final program test suite."""

    prog_class = smu75070.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['o70V'], 70.0), (sen['oYesNoFan'], True),
                    ),
                'FullLoad': (
                    (sen['o70V'], 70.0),
                    ),
                'OCP': (
                    (sen['o70V'], (70.0, ) * 15 + (69.2, ), ),
                    ),
                'Shutdown': (
                    (sen['o70V'], (10.0, 70.0)),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'FullLoad', 'OCP', 'Shutdown'],
            self.tester.ut_steps)
