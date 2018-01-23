#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC2 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class _BC2Initial(ProgramTestCase):

    """BC2 Initial program test suite."""

    prog_class = bc2.Initial
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.bc2.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.bluetooth.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], 'A1526040123'),
                    (sen['vin'], 12.0), (sen['3v3'], 3.30),
                    ),
                'TestArm': (
                    (sen['arm_swver'], bc2.config.SW_VERSION),
                    ),
                'Bluetooth': (
                    (sen['btmac'], self.btmac),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth'], self.tester.ut_steps)


class BC2_Initial(_BC2Initial):

    """BC2 Initial program test suite."""

    parameter = 'STD'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2 program."""
        super()._pass_run()


class BC2H_Initial(_BC2Initial):

    """BC2H Initial program test suite."""

    parameter = 'H'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2H program."""
        super()._pass_run()
