#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Drifter Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import drifter


class DrifterFinal(ProgramTestCase):

    """Drifter Final program test suite."""

    prog_class = drifter.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'DisplayCheck': (
                    (sen['oYesNoSeg'], True),
                    (sen['oYesNoBklight'], True),
                    (sen['oYesNoDisplay'], True),
                    ),
                'SwitchCheck': (
                    (sen['oNotifySwOff'], True), (sen['oWaterPump'], 0.1),
                    (sen['oBattSw'], 0.1), (sen['oNotifySwOn'], True),
                    (sen['oWaterPump'], 11.0), (sen['oBattSw'], 11.0),
                    (sen['oUSB5V'], 5.0),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(['DisplayCheck', 'SwitchCheck'], self.tester.ut_steps)
