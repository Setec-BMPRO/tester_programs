#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class _CommonInitial(ProgramTestCase):

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
        patcher = patch('share.bluetooth.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], 'A1526040123'),
                    (sen['tstpin_cover'], 0.0),
                    (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    (sen['brake'], (0.0, 12.0)),
                    ),
                'Operation': (
                    (sen['light'], (11.9, 0.0)),
                    (sen['remote'], (self.remote_out, 0.0)),
                    (sen['red'], (0.0, 1.8, 0.0)),
                    (sen['green'], (0.0, 2.5, 0.0)),
                    (sen['blue'], (0.0, 2.8, 0.0)),
                    (sen['arm_SwVer'], self.test_program.sw_version),
                    (sen['arm_Fault'], 0),
                    ),
                'Calibrate': (
                    (sen['brake'], (0.2999, 0.3, 11.999, 12.0)),
                    (sen['arm_Vbatt'], (12.1, 12.001)),
                    (sen['arm_Vbrake'], (12.2, 12.002)),
                    (sen['arm_Ibrake'], 1.5),
                    (sen['arm_Vpin'], 0.1),
                    ),
                'Bluetooth': (
                    (sen['arm_BtMAC'], (self.btmac, )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(30, len(result.readings))
        self.assertEqual(
            ['Prepare', 'Operation', 'Calibrate', 'Bluetooth'],
            self.tester.ut_steps)


class TRS2_Initial(_CommonInitial):

    """TRS2 Initial program test suite."""

    parameter = 'STD'
    debug = False
    remote_out = 11.9

    def test_pass_run(self):
        super()._pass_run()


class TRS2_AS_Initial(_CommonInitial):

    """TRS2 AS Initial program test suite."""

    parameter = 'AS'
    debug = False
    remote_out = 0.0

    def test_pass_run(self):
        super()._pass_run()
