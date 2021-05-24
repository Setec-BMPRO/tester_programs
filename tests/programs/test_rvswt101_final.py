#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Final Test program."""

from unittest.mock import patch, MagicMock

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Final(ProgramTestCase):

    """RVSWT101 Final program test suite."""

    prog_class = rvswt101.Final
    parameter = '4gp1'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.bluetooth.SerialToMAC',
                'programs.rvswt101.arduino.Arduino',
                'programs.rvswt101.console.DirectConsole',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mypi = MagicMock(name='MyRasPi')
        mypi.scan_advert_blemac.return_value = {
            'ad_data': {'255': '1f050112022d624c3a00000300d1139e69'},
            'rssi': -50,
            }
        patcher = patch('share.bluetooth.RaspberryBluetooth', return_value=mypi)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Bluetooth': (          # Bluetooth TestStep
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['mirmac'], '001ec030c2be'),
                    (sen['ButtonPress'], True),
                    (sen['mirscan'], (True, ) * 6),
                    (sen['cell_voltage'], (3.31, ) * 6),
                    (sen['switch_type'], (0, ) * 6),
                    (sen['debugOn'], 'OK'),
                    (sen['debugOff'], 'OK'),
                    (sen['buttonPress_1'], 'OK'),
                    (sen['buttonPress_2'], 'OK'),
                    (sen['buttonPress_3'], 'OK'),
                    (sen['buttonPress_4'], 'OK'),
                    (sen['buttonPress_5'], 'OK'),
                    (sen['buttonPress_6'], 'OK'),
                    (sen['retractAll'], 'OK'),
                    (sen['ejectDut'], 'OK'),
                    (sen['4ButtonModel'], 'OK'),
                    (sen['6ButtonModel'], 'OK'),
                    (sen['correctSwitchPressed'], (True, ) * 6),
                    ),
                },
            }

        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)

        buttons = rvswt101.Final.additional_params['buttons']
        expected_pass_count = ( 1                 # sernum
                              + 1                 # ble_mac
                              + (1 * buttons)     # buttonPress x buttons
                              + (1 * buttons)     # scan_mac x buttons
                              + (3 * buttons))    # cell_voltage, switch_type, correct_switch_pressed (each x buttons)

        self.assertEqual(expected_pass_count, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
