#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""UnitTest for BP35 Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bp35


class BP35Final(ProgramTestCase):

    """BP35 Final program test suite."""

    prog_class = bp35.Final
    parameter = None
    debug = False
    sernum = 'A1626010123'

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'serial.Serial',
                'tester.CANTunnel',
                'programs.bp35.console.TunnelConsole',
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
                    (sen['sernum'], self.sernum),
                    (sen['vbat'], 12.8),
                    (sen['yesnogreen'], True),
                    ),
                'CAN': (
                    (sen['can12v'], 12.0),
                    (sen['arm_swver'], bp35.config.BP35.arm_sw_version),
                    (sen['notifycable'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(['PowerUp', 'CAN'], self.tester.ut_steps)
