#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS1 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trs1


class TRS1Initial(ProgramTestCase):

    """TRS1 Initial program test suite."""

    prog_class = trs1.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['oVin'], 0.0), (sen['o5V'], 0.0),
                    (sen['oBrake'], 0.0), (sen['oLight'], 0.0),
                    ),
                'BreakAway': (
                    (sen['oVin'], 12.0), (sen['o5V'], 5.0),
                    (sen['oBrake'], 12.0), (sen['oLight'], 12.0),
                    (sen['oRed'], 10.0), (sen['oYesNoGreen'], True),
                    (sen['tp3'], ((0.56,),)),
                    ),
                'BattLow': (
                    (sen['oRed'], (0.0, 10.0)),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'BreakAway', 'BattLow'], self.tester.ut_steps)
