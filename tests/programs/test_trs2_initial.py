#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSInitial(ProgramTestCase):

    """TRS2 Initial program test suite."""

    prog_class = trs2.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.trs2.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['tstpin_cover'], 0.0),
                    (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    (sen['brake'], (0.0, 12.0)),
                    ),
                'Operation': (
                    (sen['light'], (11.9, 0.0)),
                    (sen['remote'], (11.9, 0.0)),
                    (sen['red'], (3.1, 0.5, 3.1)),
                    (sen['green'], (3.1, 0.0, 3.1)),
                    (sen['blue'], (1.6, 0.25, 3.1)),
                    (sen['arm_SwVer'], (trs2.Initial.arm_version, )),
                    (sen['arm_Fault'], 0),
                    ),
                'Calibrate': (
                    (sen['brake'], (0.3, 12.0)),
                    (sen['arm_Vbatt'], 12.001),
                    (sen['arm_Vbrake'], 12.002),
                    (sen['arm_Ibrake'], 0.101),
                    (sen['arm_Vpin'], 0.102),
                    ),
                'Bluetooth': (
                    (sen['arm_BtMAC'], (self.btmac, )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(29, len(result.readings))
        self.assertEqual(
            ['Prepare', 'Operation', 'Calibrate', 'Bluetooth'],
            self.tester.ut_steps)
