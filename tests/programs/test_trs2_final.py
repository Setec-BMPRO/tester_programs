#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Final Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSFinal(ProgramTestCase):

    """TRS2 Final program test suite."""

    prog_class = trs2.Final
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.trs2.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.bluetooth.BleRadio', return_value=mybt)
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
                    (sen['tstpin_cover'], 0.0), (sen['vin'], 12.0),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Prepare', 'Bluetooth', ], self.tester.ut_steps)
