#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CN102/3 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import cn102


class CN102Initial(ProgramTestCase):

    """CN102 Initial program test suite."""

    prog_class = cn102.Initial
    parameter = '102'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'share.programmer.NRF52',
                'share.bluetooth.RaspberryBluetooth',
                'programs.cn102.console.DirectConsole',
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
                'PartCheck': (
                    (sen['microsw'], 10.0), (sen['sw1'], 10.0),
                    (sen['sw2'], 10.0),
                    ),
                'PowerUp': (
                    (sen['oSnEntry'], 'A1526040123'),
                    (sen['oVin'], 8.0), (sen['o3V3'], 3.3),
                    ),
                'TestArm': (
                    (sen['o3V3'], 3.3),
                    ),
                'TankSense': (
                    (sen['tank1'], 5),
                    (sen['tank2'], 5),
                    (sen['tank3'], 5),
                    (sen['tank4'], 5),
                    ),
                'Bluetooth': (
                    (sen['mirscan'], True),
                    ),
                'CanBus': (
                    (sen['CANBIND'], 1 << 28),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(
            ['PartCheck', 'PowerUp', 'PgmARM', 'PgmNordic', 'TestArm',
             'TankSense', 'Bluetooth', 'CanBus'],
            self.tester.ut_steps)
