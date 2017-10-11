#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TS3520 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ts3520


class TS3520Final(ProgramTestCase):

    """TS3520 Final program test suite."""

    prog_class = ts3520.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FuseCheck': (
                    (sen['oNotifyStart'], True), (sen['o12V_1'], 0.0),
                    (sen['oYesNoRed'], True), (sen['oNotifyFuse'], True),
                    ),
                'PowerUp': (
                    (sen['o12V_1'], 13.8), (sen['o12V_2'], 13.8),
                    (sen['o12V_3'], 13.8), (sen['oYesNoGreen'], True),
                    ),
                'FullLoad': (
                    (sen['o12V_1'], 13.6),
                    ),
                'OCP': (
                    (sen['o12V_1'], (13.4, ) * 15 + (13.0, ), ),
                    ),
                'Poweroff': (
                    (sen['oNotifyMains'], True), (sen['o12V_1'], 0.0),
                    (sen['oYesNoOff'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(
            ['FuseCheck', 'PowerUp', 'FullLoad', 'OCP', 'Poweroff'],
            self.tester.ut_steps)
