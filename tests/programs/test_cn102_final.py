#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CN102/3 Final Test program."""

from unittest.mock import patch, Mock

from ..data_feed import UnitTester, ProgramTestCase
from programs import cn102


class CN102Final(ProgramTestCase):

    """CN102/3 Final program test suite."""

    prog_class = cn102.Final
    parameter = '103'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        # BLE scanner
        mypi = Mock(name='MyRasPi')
        mypi.scan_advert_sernum.return_value = {'ad_data': '', 'rssi': -50}
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
                'Bluetooth': (
                    (sen['sernum'], 'A2026040123'),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
