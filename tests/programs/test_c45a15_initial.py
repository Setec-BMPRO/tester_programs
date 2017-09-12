#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for C45A-15 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import c45a15


class C45A15Initial(ProgramTestCase):

    """C45A-15 Initial program test suite."""

    prog_class = c45a15.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock': (
                    (sen['oLock'], 10.0),
                    ),
                'SecCheck': (
                    (sen['oVoutPre'], 12.0), (sen['oVsense'], (0.5, 12.0)),
                    (sen['oVout'], (12.0, 12.0)), (sen['oVref'], 5.0),
                    ),
                'OVP': (
                    (sen['oVref'], 0.5), (sen['oGreen'], 2.0),
                    (sen['oVcc'], (12.0, ) * 25 + (5.4, ), ),
                    ),
                'PowerUp': (
                    (sen['oVac'], (96, 240)), (sen['oVcc'], 12.0),
                    (sen['oVref'], 5.0), (sen['oGreen'], 2.0),
                    (sen['oYellow'], (0.1, 2.0)), (sen['oRed'], (0.1, 4.5)),
                    (sen['oVout'], (9.0,) * 2 + (16.0,)),
                    (sen['oVsense'], 8.9),
                    ),
                'Load': (
                    (sen['oVout'], (16.0, 15.8)),
                    ),
                'OCP': (
                    (sen['oVout'], (16.0, ) * 65 + (15.5, ), ),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(28, len(result.readings))
        self.assertEqual(
            ['FixtureLock', 'SecCheck', 'OVP', 'PowerUp', 'Load', 'OCP'],
            self.tester.ut_steps)
