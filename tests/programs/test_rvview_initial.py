#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVVIEW Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvview


class RvViewInitial(ProgramTestCase):

    """RVVIEW Initial program test suite."""

    prog_class = rvview.Initial
    parameter = None
    debug = False
    sernum = 'A1626010123'

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.rvview.console.TunnelConsole',
                'programs.rvview.console.DirectConsole',
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
                    (sen['oSnEntry'], self.sernum),
                    (sen['oVin'], 7.5),
                    (sen['o3V3'], 3.3),
                    ),
                'Initialise': (
                    (sen['oSwVer'], rvview.config.SW_VERSION),
                    ),
                'Display': (
                    (sen['oYesNoOn'], True),
                    (sen['oYesNoOff'], True),
                    (sen['oBkLght'], (3.0, 0.0)),
                    ),
                'CanBus': (
                    (sen['oCANBIND'], 1 << 28),
                    (sen['TunnelSwVer'], rvview.config.SW_VERSION),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'Initialise', 'Display', 'CanBus'],
            self.tester.ut_steps)
