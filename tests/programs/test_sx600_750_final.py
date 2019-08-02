#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SX600/750 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import sx600_750


class SX600Final(ProgramTestCase):

    """SX600 Final program test suite."""

    prog_class = sx600_750.Final
    parameter = '600'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['oIec'], (0.0, 240.0)), (sen['o5v'], 5.1),
                    (sen['o12v'], 0.0), (sen['oYesNoGreen'], True),
                    ),
                'PowerOn': (
                    (sen['oYesNoBlue'], True), (sen['o5v'], 5.1),
                    (sen['oPwrGood'], 0.1), (sen['oAcFail'], 5.1),
                    ),
                'Load': (
                    (sen['o5v'], 5.1), (sen['o12v'], (12.1, 12.0)),
                    (sen['o24v'], (24.1, 24.0)), (sen['oPwrGood'], 0.1),
                    (sen['oAcFail'], 5.1),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(['PowerUp', 'PowerOn', 'Load'], self.tester.ut_steps)


class SX750Final(ProgramTestCase):

    """SX750 Final program test suite."""

    prog_class = sx600_750.Final
    parameter = '750'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'InputRes':(
                    (sen['oInpRes'], 70000),
                    ),
                'PowerUp': (
                    (sen['oIec'], (0.0, 240.0)), (sen['o5v'], 5.1),
                    (sen['o12v'], 0.0), (sen['oYesNoGreen'], True),
                    ),
                'PowerOn': (
                    (sen['oYesNoBlue'], True), (sen['o5v'], 5.1),
                    (sen['oPwrGood'], 0.1), (sen['oAcFail'], 5.1),
                    ),
                'Load': (
                    (sen['o5v'], 5.1), (sen['o12v'], (12.2, 12.1)),
                    (sen['o24v'], (24.2, 24.1)), (sen['oPwrGood'], 0.1),
                    (sen['oAcFail'], 5.1),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(19, len(result.readings))
        self.assertEqual(
            ['InputRes', 'PowerUp', 'PowerOn', 'Load'], self.tester.ut_steps)
