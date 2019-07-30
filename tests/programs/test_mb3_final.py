#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for MB3 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import mb3


class MB3Final(ProgramTestCase):

    """MB3 Final program test suite."""

    prog_class = mb3.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerOn': (
                    (sen['vaux'], (13.0, 8.0)),
                    (sen['yesnolight'], True),
                    (sen['vbat'], 14.4),
                    (sen['yesnooff'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(['PowerOn', ], self.tester.ut_steps)
