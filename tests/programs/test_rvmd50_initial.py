#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMD50 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmd50


class RVMD50Initial(ProgramTestCase):

    """RVMD50 Initial program test suite."""

    prog_class = rvmd50.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['vin'], 7.5),
                    (sen['3v3'], 3.3),
                    ),
                'Display': (
                    (sen['bklght'], (0.0, 3.0)),
                    (sen['YesNoDisplay'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'Display'],
            self.tester.ut_steps)
