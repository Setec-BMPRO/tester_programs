#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CN101 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import cn101


class CN101Initial(ProgramTestCase):

    """CN101 Initial program test suite."""

    prog_class = cn101.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.ProgramARM',
                'programs.cn101.console.DirectConsole',
                'programs.cn101.console.TunnelConsole',
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
                'PartCheck': (
                    (sen['microsw'], 10.0), (sen['sw1'], 10.0),
                    (sen['sw2'], 10.0),
                    ),
                'PowerUp': (
                    (sen['oSnEntry'], 'A1526040123'),
                    (sen['oVin'], 8.0), (sen['o3V3'], 3.3),
                    ),
                'TestArm': (
                    (sen['oSwVer'], cn101.config.SW_VERSION),
                    ),
                'TankSense': (
                    (sen['tank1'], 5),
                    (sen['tank2'], 5),
                    (sen['tank3'], 5),
                    (sen['tank4'], 5),
                    ),
                'Bluetooth': (
                    (sen['oBtMac'], self.btmac),
                    ),
                'CanBus': (
                    (sen['oCANBIND'], 1 << 28),
                    (sen['TunnelSwVer'], cn101.config.SW_VERSION),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(15, len(result.readings))
        self.assertEqual(
            ['PartCheck', 'PowerUp', 'Program', 'TestArm',
             'TankSense', 'Bluetooth', 'CanBus'],
            self.tester.ut_steps)
