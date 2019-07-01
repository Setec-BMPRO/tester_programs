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
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mypi = MagicMock(name='MyRasPi')
        mypi.scan_advert_blemac.return_value = [
            [255, 'Manufacturer', '1f050112022d624c3a00000300d1139e69']
            ]
        patcher = patch('share.bluetooth.RaspberryBluetooth', return_value=mypi)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Bluetooth': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['mirmac'], '001ec030c2be'),
                    (sen['ButtonPress'], True),
                    (sen['mirscan'], True),
                    (sen['cell_voltage'], 3.31),
                    (sen['switch_type'], 1),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
