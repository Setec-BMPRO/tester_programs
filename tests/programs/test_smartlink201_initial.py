#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SmartLink201 Initial Test program."""

from unittest.mock import MagicMock, patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import smartlink201


class SmartLink201Initial(ProgramTestCase):

    """SmartLink201 Initial program test suite."""

    prog_class = smartlink201.Initial
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.bluetooth.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.ARM',
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'share.bluetooth.SerialToMAC',
                'programs.smartlink201.console.Console',
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
                    (sen['SnEntry'], 'A2126010123'),
                    (sen['photosense'], 0.0),
                    (sen['Vbatt'], 12.0),
                    (sen['Vin'], 10.0),
                    (sen['3V3'], 3.3),
                    ),
                'Nordic': (
                    (sen['3V3'], 3.3),
                    (sen['SL_MAC'], 'aabbccddeeff'),
                    (sen['SL_SwVer'], smartlink201.config.sw_nrf_version),
                    ),
                'Calibrate': (
                    (sen['Vbatt'], 12.01),
                    (sen['SL_Vbatt'], ('12120', '12020', )),
                    ),
                'TankSense': (
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(11, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmARM', 'PgmNordic',
             'Nordic', 'Calibrate', 'TankSense', ],
            self.tester.ut_steps)
