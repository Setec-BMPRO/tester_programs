#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""UnitTest for BP35 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bp35


class BP35Final(ProgramTestCase):

    """BP35 Final program test suite."""

    prog_class = bp35.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['vbat'], 12.8),
                    (sen['yesnogreen'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(['PowerUp'], self.tester.ut_steps)
