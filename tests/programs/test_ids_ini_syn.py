#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 SynBuck Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialSyn(ProgramTestCase):

    """IDS500 SynBuck Initial program test suite."""

    prog_class = ids500.InitialSyn
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.ProgramPIC')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['o20VT'], 20.0), (sen['o_20V'], -20.0),
                    (sen['o9V'], 11.0), (sen['oTec'], 0.0),
                    (sen['oLdd'], 0.0), (sen['oLddVmon'], 0.0),
                    (sen['oLddImon'], 0.0), (sen['oTecVmon'], 0.0),
                    (sen['oTecVset'], 0.0),
                    ),
                'Program': (
                    (sen['olock'], 10.0),
                    ),
                'TecEnable': (
                    (sen['oTecVmon'], (0.5, 2.5, 5.0)),
                    (sen['oTec'], (0.5, 7.5, 15.0)),
                    ),
                'TecReverse': (
                    (sen['oTecVmon'], (5.0,) * 2),
                    (sen['oTec'], (-15.0, 15.0)),
                    ),
                'LddEnable': (
                    (sen['oLdd'], (0.0, 0.65, 1.3)),
                    (sen['oLddShunt'], (0.0, 0.006, 0.05)),
                    (sen['oLddImon'], (0.0, 0.6, 5.0)),
                    ),
                'ISSetAdj': (
                    (sen['oLddIset'], 5.01), (sen['oAdjLdd'], True),
                    (sen['oLddShunt'], (0.0495, 0.0495, 0.05005)),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(32, len(result.readings))
        self.assertEqual(
            ['Program', 'PowerUp', 'TecEnable', 'TecReverse',
             'LddEnable', 'ISSetAdj'],
            self.tester.ut_steps)
