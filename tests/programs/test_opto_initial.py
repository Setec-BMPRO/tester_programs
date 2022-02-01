#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Opto Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import opto_test


class OptoInitial(ProgramTestCase):

    """Opto Initial program test suite."""

    prog_class = opto_test.Initial
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('smtplib.SMTP')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        oa1 = ()
        oa10 = ()
        for opto in range(opto_test.Initial._opto_count):
            oa1 += (
                (sen['Vce'][opto], (-5.3, -4.9, -5.02, -5.02)),
                (sen['Iout'][opto], 0.6),
                )
            oa10 += (
                (sen['Vce'][opto], (-5.5, -4.8, -5.2, -4.94, -5.02, -5.02)),
                (sen['Iout'][opto], 15.0),
                )
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'BoardNum': (
                    (sen['sernum'], 'A2201770001'),
                    ),
                'InputAdj1': (
                    (sen['Isense'], (0.5, ) * 5 + (1.0, 1.003), ),
                    ),
                'OutputAdj1': oa1 + (
                    (sen['Isense'], (1.003, ) * opto_test.Initial._opto_count),
                    ),
                'InputAdj10': (
                    (sen['Isense'], (5.0, ) * 5 + (10.0, 10.03), ),
                    ),
                'OutputAdj10': oa10 + (
                    (sen['Isense'], (10.03, ) * opto_test.Initial._opto_count),
                    ),
                'Email': (
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(205, len(result.readings))
        self.assertEqual(
            ['BoardNum',
             'InputAdj1', 'OutputAdj1', 'InputAdj10', 'OutputAdj10',
             'Email', ],
            self.tester.ut_steps)
