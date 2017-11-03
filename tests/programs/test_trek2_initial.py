#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2


class Trek2Initial(ProgramTestCase):

    """Trek2 Initial program test suite."""

    prog_class = trek2.Initial
    parameter = None
    debug = False
    sernum = 'A1526040123'

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.trek2.console.DirectConsole',
                'programs.trek2.console.TunnelConsole',
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
                    (sen['oSnEntry'],
                    (self.sernum, )),
                    (sen['oVin'], 12.0),
                    (sen['o3V3'], 3.3),
                    ),
                'TestArm': (
                    (sen['SwVer'], (trek2.config.SW_VERSION, )),
                    ),
                'CanBus': (
                    (sen['oCANBIND'], 1 << 28),
                    (sen['TunnelSwVer'], (trek2.config.SW_VERSION, )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'TestArm', 'CanBus'], self.tester.ut_steps)
