#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for ATXG450-2V Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import atxg450


class ATXG4502VFinal(ProgramTestCase):

    """ATXG450-2V Final program test suite."""

    prog_class = atxg450.Final2V
    parameter = None
    debug = True # False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    ((sen['o5Vsb'], 5.10), (sen['oYesNoGreen'], True),
                     (sen['o24V'], 0.0), (sen['o12V'], 0.0), (sen['o5V'], 0.0),
                     (sen['o3V3'], 0.0), (sen['on12V'], 0.0),
                     (sen['oPwrGood'], 0.1), (sen['oPwrFail'], 5.0), )
                    ),
                'SwitchOn': (
                    ((sen['o24V'], 24.0), (sen['o12V'], 12.0),
                     (sen['o5V'], 5.0), (sen['o3V3'], 3.3),
                     (sen['on12V'], -12.0), (sen['oPwrGood'], 5.0),
                     (sen['oPwrFail'], 0.1), (sen['oYesNoFan'], True), )
                    ),
                'FullLoad': (
                    ((sen['o5Vsb'], 5.10), (sen['o24V'], 24.0),
                     (sen['o12V'], 12.0), (sen['o5V'], 5.0),
                     (sen['o3V3'], 3.3), (sen['on12V'], -12.0),
                     (sen['oPwrGood'], 5.0), (sen['oPwrFail'], 0.1), )
                    ),
                'OCP24': (
                    ((sen['o24V'], (24.1, ) * 15 + (22.0, ), ), )
                    ),
                'OCP12': (
                    ((sen['o12V'], (12.1, ) * 15 + (11.0, ), ), )
                    ),
                'OCP5': (
                    ((sen['o5V'], (5.1, ) * 15 + (4.0, ), ), )
                    ),
                'OCP3': (
                    ((sen['o3V3'], (3.3, ) * 15 + (3.0, ), ), )
                    ),
                'OCP5sb': (
                    ((sen['o5Vsb'], (5.1, ) * 10 + (4.0, ), ), )
                    ),
                'PowerFail': (
                    ((sen['oPwrFail'], 5.05), )
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(31, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'SwitchOn', 'FullLoad',
             'OCP24', 'OCP12', 'OCP5', 'OCP3', 'OCP5sb',
             'PowerFail'],
            self.tester.ut_steps)