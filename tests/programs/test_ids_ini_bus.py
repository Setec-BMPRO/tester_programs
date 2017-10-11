#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Bus Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialBus(ProgramTestCase):

    """IDS500 Bus Initial program test suite."""

    prog_class = ids500.InitialBus
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['olock'], 0.0),
                    (sen['o400V'], 400.0),
                    ),
                'TecLddStartup': (
                    (sen['o20VT'], (23, 23, 22, 19)),
                    (sen['o9V'], (11, 10, 10, 11 )),
                    (sen['o20VL'], (23, 23, 21, 23)),
                    (sen['o_20V'], (-23, -23, -21, -23)),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(['PowerUp', 'TecLddStartup'], self.tester.ut_steps)
