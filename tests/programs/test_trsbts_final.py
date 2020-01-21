#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS-BTS Final Test program."""

from unittest.mock import patch, MagicMock
from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTSFinal(ProgramTestCase):

    """TRS-BTS Final program test suite."""

    prog_class = trsbts.Final
    parameter = None
    debug = False

#    def setUp(self):
#        """Per-Test setup."""
#        for target in (
#                'share.bluetooth.RaspberryBluetooth',
#                ):
#            patcher = patch(target)
#            self.addCleanup(patcher.stop)
#            patcher.start()
#        super().setUp()

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
                    (sen['sernum'], 'A1526040123'),
                    (sen['vbat'], 12.0),
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
        self.assertEqual(5, len(result.readings))
        self.assertEqual(['Bluetooth', ], self.tester.ut_steps)
