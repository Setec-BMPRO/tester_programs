#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for ODL104 Final Test program."""

from unittest.mock import patch, Mock

from ..data_feed import UnitTester, ProgramTestCase
from programs import odl104


class ODL104Final(ProgramTestCase):

    """ODL104 Final program test suite."""

    prog_class = odl104.Final
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.bluetooth.SerialToMAC',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mypi = Mock(name='MyRasPi')
        mypi.scan_advert_blemac.return_value = {
            'ad_data': {255: 'databytes'},
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
                    (sen['sernum'], 'A2226010123'),
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
