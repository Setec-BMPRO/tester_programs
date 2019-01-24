#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Initial(ProgramTestCase):

    """RVSWT101 Initial program test suite."""

    prog_class = rvswt101.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.bluetooth.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'programs.cn102.console.DirectConsole',
                'programs.cn102.console.TunnelConsole',
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
                    (sen['oSnEntry'], 'A1526040123'),
                    (sen['oVin'], 8.0),
                    ),
                'TestArm': (
                    (sen['SwVer'], rvswt101.config.RVSWT101.sw_arm_version),
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
        self.assertEqual(15, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmNordic', 'TestArm', 'Bluetooth'],
            self.tester.ut_steps)
