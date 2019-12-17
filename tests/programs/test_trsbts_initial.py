#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS-BTS Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTS_Initial(ProgramTestCase):

    """TRS-BTS Initial program test suite."""

    prog_class = trsbts.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""

        for target in (
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'share.bluetooth.SerialToMAC',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mycon = MagicMock(name='MyConsole')
        mycon.get_mac.return_value = '001ec030c2be'
        patcher = patch(
            'programs.trsbts.console.Console', return_value=mycon)
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
                    (sen['vin'], 8.0),
                    (sen['3v3'], 3.30),
                    (sen['chem'], 3.0),
                    (sen['sway-'], 2.0),
                    (sen['sway+'], 1.0),
                    (sen['light'], (0.0, 12.0)),
                    (sen['brake'], (0.0, 12.0)),
                    ),
                'Operation': (
                    (sen['remote'], (11.9, 0.0)),
                    (sen['red'], (0.0, 1.8, 0.0)),
                    (sen['green'], (0.0, 2.5, 0.0)),
                    (sen['blue'], (0.0, 2.8, 0.0)),
                    (sen['arm_swver'], trsbts.config.SW_VERSION),
                    ),
                'Calibrate': (
                    (sen['arm_vbatt'], (12.4, 12.1)),
                    (sen['vbat'], (12.0, 12.0)),
                    (sen['arm_vpin'], 0.1),
                    ),
                'Bluetooth': (
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(27, len(result.readings))
        self.assertEqual(
            ['Prepare', 'PgmNordic', 'Operation', 'Calibrate', 'Bluetooth'],
            self.tester.ut_steps)
