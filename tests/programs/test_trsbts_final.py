#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS-BTS Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTSFinal(ProgramTestCase):

    """TRS-BTS Final program test suite."""

    prog_class = trsbts.Final
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.bluetooth.RaspberryBluetooth',
                'programs.trsbts.console.Console',
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
                'Prepare': (
                    (sen['sernum'], 'A1526040123'),
                    (sen['vin'], 12.0),
                    ),
                'Bluetooth': (
                    (sen['mirscan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(['Prepare', 'Bluetooth', ], self.tester.ut_steps)
