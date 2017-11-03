#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2 Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2


class Trek2Final(ProgramTestCase):

    """Trek2 Final program test suite."""

    prog_class = trek2.Final
    parameter = None
    debug = True

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.trek2.console.TunnelConsole',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _tank_sensors(self, value):
        """Fill all tank sensors with a value."""
        for sen in self.test_program.sensors['otanks']:
            sen.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Display': (
                    (sen['SwVer'], (trek2.config.SW_VERSION, )),
                    (sen['oYesNoSeg'], True),
                    (sen['oYesNoBklight'], True),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'Tanks': (
                    self._tank_sensors, (1, 2, 3, 4)
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(19, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'TunnelOpen', 'Display', 'Tanks'],
            self.tester.ut_steps)
