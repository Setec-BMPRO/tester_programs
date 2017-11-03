#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BLE2CAN Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ble2can


class BLE2CANInitial(ProgramTestCase):

    """BLE2CAN Initial program test suite."""

    prog_class = ble2can.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.ble2can.console.Console')
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
                    (sen['3v3'], 3.30),
                    ),
                'TestArm': (
                    (sen['red'], (3.1, 0.5, 3.1, )),
                    (sen['green'], (3.1, 0.0, 3.1, )),
                    (sen['blue'], (3.1, 0.25, 3.1, )),
                    (sen['arm_SwVer'], ble2can.config.SW_VERSION),
                    ),
                'Bluetooth': (
                    (sen['arm_BtMAC'], self.btmac),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(16, len(result.readings))
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth'], self.tester.ut_steps)
