#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for C15A-15 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import c15a15


class C15A15Initial(ProgramTestCase):

    """C15A-15 Initial program test suite."""

    prog_class = c15a15.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Power90':
                    ((sen['vin'], 90.0), (sen['vbus'], 130),
                     (sen['vcc'], 9), (sen['vout'], 15.5),
                     (sen['green'], 11), (sen['yellow'], 0.2), ),
                'Power240':
                    ((sen['vin'], 240.0), (sen['vbus'], 340),
                     (sen['vcc'], 12), (sen['vout'], 15.5),
                     (sen['green'], 11), (sen['yellow'], 0.2), ),
                'OCP':
                    ((sen['vout'], (15.5, ) * 15 + (13.5, ), ),
                     (sen['yellow'], 8), (sen['green'], 9),
                     (sen['vout'], (10, 15.5)), ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(
            ['Power90', 'Power240', 'OCP', 'PowerOff'],
            self.tester.ut_steps)

    def test_fail_run(self):
        """FAIL 1st Vbat reading."""
        # Patch threading.Event & threading.Timer to remove delays
        mymock = MagicMock()
        mymock.is_set.return_value = True   # threading.Event.is_set()
        patcher = patch('threading.Event', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('threading.Timer', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Power90':
                    ((sen['vin'], 10.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['Power90'], self.tester.ut_steps)
