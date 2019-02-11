#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMC101 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmc101


class RVMC101Initial(ProgramTestCase):

    """RVMC101 Initial program test suite."""

    prog_class = rvmc101.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mycon = MagicMock(name='MyConsole')
        mycon.get_mac.return_value = '001ec030c2be'
        patcher = patch(
            'programs.rvmc101.console.Console', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'programs.rvmc101.config.SerialToMAC',
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
                'PowerUp': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['vin'], 3.3),
                    ),
                'Bluetooth': (
                    (sen['mirscan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmNordic', 'GetMac', 'Bluetooth'],
            self.tester.ut_steps)
