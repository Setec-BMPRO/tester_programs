#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2/JControl Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2_jcontrol


class _CommonFinal(ProgramTestCase):

    """Trek2/JControl Final program test suite."""

    prog_class = trek2_jcontrol.Final

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.trek2_jcontrol.console.TunnelConsole',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _tank_sensors(self, value):
        """Fill all tank sensors with a value."""
        for sen in self.test_program.sensors['otanks']:
            sen.store(value)

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Display': (
                    (sen['SwVer'], self.test_program.config['BinVer']),
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


class Trek2_Final(_CommonFinal):

    """Trek2 Final program test suite."""

    parameter = 'TK2'
    debug = False

    def test_pass_run(self):
        """PASS run of the Trek2 program."""
        super()._pass_run()


class JControl_Final(_CommonFinal):

    """JControl Final program test suite."""

    parameter = 'JC'
    debug = False

    def test_pass_run(self):
        """PASS run of the JControl program."""
        super()._pass_run()