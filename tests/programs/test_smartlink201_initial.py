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
                'programs.smartlink201.console.DirectConsole',
                'programs.smartlink201.console.TunnelConsole',
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
                    (sen['oSnEntry'], 'A1526040123'),
                    (sen['photosense'], 0.0),
                    (sen['oVin'], 8.0), (sen['o3V3'], 3.3),
                    ),
                'TestArm': (
                    (sen['o3V3'], 3.3),
                    (sen['SwVer'],
                     smartlink201.config.sw_arm_version),
                    ),
                'TankSense': (
                    (sen['tank1'], 5),
                    (sen['tank2'], 5),
                    (sen['tank3'], 5),
                    (sen['tank4'], 5),
                    ),
                'Bluetooth': (
                    (sen['mirscan'], True),
                    ),
                'CanBus': (
                    (sen['CANBIND'], 1 << 28),
                    (sen['TunnelSwVer'],
                     smartlink201.config.sw_arm_version),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmARM', 'PgmNordic', 'TestArm',
             'TankSense', 'Bluetooth', 'CanBus'],
            self.tester.ut_steps)
