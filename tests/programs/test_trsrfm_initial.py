#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS-RFM Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trsrfm


class TRSRFMInitial(ProgramTestCase):

    """TRS-RFM Initial program test suite."""

    prog_class = trsrfm.Initial
    parameter = None
    debug = False
    btmac = '001ec030bc15'

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.Nordic',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        # Console
        mycon = MagicMock(name='MyConsole')
        mycon.get_mac.return_value = self.btmac
        patcher = patch(
            'programs.trsrfm.console.Console', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        # BLE scanner
        mypi = MagicMock(name='MyRasPi')
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
                    (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    ),
                'Operation': (
                    (sen['red'], (3.1, 0.5, 3.1, )),
                    (sen['green'], (3.1, 0.0, 3.1, )),
                    (sen['blue'], (3.1, 0.25, 3.1, )),
                    (sen['arm_SwVer'], trsrfm.config.SW_VERSION),
                    ),
                'Bluetooth': (
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(15, len(result.readings))
        self.assertEqual(
            ['Prepare', 'PgmNordic', 'Operation', 'Bluetooth'],
            self.tester.ut_steps)
