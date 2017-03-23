#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SMU750-70 Initial Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import smu75070


class SMU75070Initial(ProgramTestCase):

    """SMU750-70 Initial program test suite."""

    prog_class = smu75070.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect': (
                    (sen['lock'], 10.0), (sen['inrush'], 150.0),
                    ),
                'PowerOn': (
                    (sen['vac'], 100.0), (sen['vdd'], (12.0,) * 2),
                    (sen['vsecctl'], (13.0,) * 2), (sen['vbus'], (400.0, 0)),
                    (sen['vout'], 69.0),
                    ),
                'AdjOutput': (
                    (sen['vac'], 240.0), (sen['vdd'], 12.0),
                    (sen['vsecctl'], 13.0), (sen['adj_vout'], True),
                    (sen['vout'], (69.0, 69.1, 69.2, 70.0)),
                    ),
                'FullLoad': (
                    (sen['vbus'], 400.0), (sen['vdd'], 12.0),
                    (sen['vsecctl'], 13.0), (sen['vout'], 70.0),
                    ),
                'OCP': (
                    (sen['vout'], 70.0),
                    (sen['vout'], (70.0, ) * 5 + (69.0, ), ),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(21, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PartDetect', 'PowerOn', 'AdjOutput', 'FullLoad', 'OCP'],
            self.tester.ut_steps)
