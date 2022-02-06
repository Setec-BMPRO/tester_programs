#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BLE2CAN Initial Test program."""

from unittest.mock import Mock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ble2can


class BLE2CANInitial(ProgramTestCase):

    """BLE2CAN Initial program test suite."""

    prog_class = ble2can.Initial
    parameter = None
    debug = False
    btmac = '00:1E:C0:30:BC:15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.ble2can.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        mypi = Mock(name='MyRasPi')
        mypi.scan_advert_blemac.return_value = {'ad_data': '', 'rssi': -50}
        patcher = patch(
            'share.bluetooth.RaspberryBluetooth', return_value=mypi)
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
                    (sen['3v3'], 3.30), (sen['5v'], 5.0),
                    ),
                'TestArm': (
                    (sen['red'], (3.1, 0.5, 3.1, )),
                    (sen['green'], (3.1, 0.0, 3.1, )),
                    (sen['blue'], (3.1, 0.25, 3.1, )),
                    (sen['SwVer'], self.test_program.sw_version),
                    ),
                'Bluetooth': (
                    (sen['BtMac'], self.btmac),
                    ),
                'CanBus': (
                    (sen['CANbind'], 1 << 28),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth', 'CanBus'], self.tester.ut_steps)
