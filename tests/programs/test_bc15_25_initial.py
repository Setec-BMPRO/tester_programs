#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15/25 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bc15_25


class _BC15_25_Initial(ProgramTestCase):

    """BC15/25 Initial program test suite."""

    prog_class = bc15_25.Initial

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.bc15_25.console.Console',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _pass_run(self, ocp_steps):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect': (
                    (sen['lock'], 0.0), (sen['fanshort'], 3300.0),
                    ),
                'Program': (
                    (sen['3V3'], 3.3),
                    ),
                'Initialise': (
                    (sen['arm_swver'], self.test_program.config['BinVersion']),
                    ),
                'PowerUp': (
                    (sen['ACin'], 240.0), (sen['Vbus'], 330.0),
                    (sen['12Vs'], 12.0), (sen['5Vs'], 5.0),
                    (sen['3V3'], 3.3), (sen['15Vs'], 15.0),
                    (sen['Vout'], 0.2),
                    ),
                'Output': (
                    (sen['Vout'], 14.40), (sen['Vout'], 14.40),
                    (sen['arm_vout'], 14432),
                    (sen['arm_iout'], 1987),
                    (sen['arm_switch'], 3),
                    ),
                'OCP': (
                    (sen['Vout'],
                        (14.4, ) * 10 + (11.0, )
                        + (14.4, ) * 3
                        + (14.4, ) * ocp_steps + (11.0, )
                        ),
                    (sen['arm_vout'], 14400),
                    (sen['arm_iout'],
                     round(1000 * 0.8 * self.test_program.config['OCP_Nominal'])),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(23, len(result.readings))
        self.assertEqual(
            ['PartDetect', 'Program', 'Initialise', 'PowerUp',
             'Output', 'OCP'],
            self.tester.ut_steps)


class BC15_Initial(_BC15_25_Initial):

    """BC15 Initial program test suite."""

    parameter = '15'
    debug = False
    cal_lines = 39

    def test_pass_run(self):
        """PASS run of the BC15 program."""
        super()._pass_run(24)


class BC25_Initial(_BC15_25_Initial):

    """BC25 Initial program test suite."""

    parameter = '25'
    debug = False
    cal_lines = 43

    def test_pass_run(self):
        """PASS run of the BC25 program."""
        super()._pass_run(39)
