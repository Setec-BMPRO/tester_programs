#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Final Test program."""

from unittest.mock import patch, MagicMock

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Final(ProgramTestCase):

    """RVSWT101 Final program test suite."""

    prog_class = rvswt101.Final
    parameter = '6gp1'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'tester.BLE',
                'programs.rvswt101.arduino.Arduino',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mypi = MagicMock(name='decoder')
        mypi.scan_count = 6
        mypi.read.return_value = (
            -50, '1f050112022d624c3a00000300d1139e69',
            )
        patcher = patch('programs.rvswt101.device.RVSWT101', return_value=mypi)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Bluetooth': (          # Bluetooth TestStep
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['mirmac'], '001ec030c2be'),
                    (sen['cell_voltage'], (3.31, ) * 6),
                    (sen['switch_type'], (2, ) * 6),
                    (sen['buttonPress_1'], 'OK'),
                    (sen['buttonPress_2'], 'OK'),
                    (sen['buttonPress_3'], 'OK'),
                    (sen['buttonPress_4'], 'OK'),
                    (sen['buttonPress_5'], 'OK'),
                    (sen['buttonPress_6'], 'OK'),
                    (sen['buttonRelease_1'], 'OK'),
                    (sen['buttonRelease_2'], 'OK'),
                    (sen['buttonRelease_3'], 'OK'),
                    (sen['buttonRelease_4'], 'OK'),
                    (sen['buttonRelease_5'], 'OK'),
                    (sen['buttonRelease_6'], 'OK'),
                    (sen['switch_1_measure'], 16),
                    (sen['switch_2_measure'], 32),
                    (sen['switch_3_measure'], 8),
                    (sen['switch_4_measure'], 64),
                    (sen['switch_5_measure'], 4),
                    (sen['switch_6_measure'], 128),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
