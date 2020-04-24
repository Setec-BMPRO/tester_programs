#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""UnitTest for RVMN101 Final Test program."""

from unittest.mock import patch, MagicMock

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmn101


class RVMN101Final(ProgramTestCase):

    """RVMN101 Final program test suite."""

    prog_class = rvmn101.Final
    parameter = '101A'
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
        mypi.scan_advert_blemac.return_value = {
            'ad_data': {255: '1f050112022d624c3a00000300d1139e69'},
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
                'Bluetooth': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['mirmac'], '001ec030c2be'),
                    (sen['mirscan'], True),
                    (sen['mirrssi'], -50),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
