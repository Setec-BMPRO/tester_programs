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
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.trs2.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('share.BleRadio', new=self._makebt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _makebt(self, x):
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        return mybt

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['tstpin_cover'], 0.0),
                    (sen['vin'], 12.0),
                    ),
                'Bluetooth': (
                    (sen['btmac'], self.btmac),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Prepare', 'Bluetooth', ], self.tester.ut_steps)
