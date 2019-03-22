#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Final Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Final(ProgramTestCase):

    """RVSWT101 Final program test suite."""

    prog_class = rvswt101.Final
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.bluetooth.RaspberryBluetooth',
                'programs.rvswt101.config.SerialToMAC',
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
                'Bluetooth': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['mirmac'], '001ec030c2be'),
                    (sen['ButtonPress'], True),
                    (sen['mirscan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Bluetooth'], self.tester.ut_steps)
