#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMC101x Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmc101


class _RVMC101Initial(ProgramTestCase):

    """RVMC101x Initial program test suite."""

    prog_class = rvmc101.Initial
    per_panel = 4

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'share.programmer.JLink',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()


class RVMC101Initial(_RVMC101Initial):

    """RVMC101x Initial program test suite."""

    parameter = 'NXP'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['vin'], 12.0),
                    (sen['a_5v'], 5.01),
                    (sen['a_3v3'], 3.31),
                    (sen['b_5v'], 5.02),
                    (sen['b_3v3'], 3.32),
                    (sen['c_5v'], 5.03),
                    (sen['c_3v3'], 3.33),
                    (sen['d_5v'], 5.04),
                    (sen['d_3v3'], 3.34),
                    ),
                'Display': (
                    (sen['yesnodisplay'], (True, True, True, True, )),
                    ),
                'CanBus': (
                    (sen['MirCAN'], (True, True, True, True, )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(
            tuple('UUT{0}'.format(uut)
                for uut in range(1, self.per_panel + 1)))
        for res in self.tester.ut_result:
            self.assertEqual('P', res.code)
            self.assertEqual(8, len(res.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'Display', 'CanBus'],
            self.tester.ut_steps)


class RVMC101InitialLite(_RVMC101Initial):

    """RVMC101x Lite Initial program test suite."""

    parameter = 'LITE'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['vin'], 12.0),
                    (sen['a_5v'], 5.01),
                    (sen['b_5v'], 5.02),
                    (sen['c_5v'], 5.03),
                    (sen['d_5v'], 5.04),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(
            tuple('UUT{0}'.format(uut)
                for uut in range(1, self.per_panel + 1)))
        for res in self.tester.ut_result:
            self.assertEqual('P', res.code)
            self.assertEqual(2, len(res.readings))
        self.assertEqual(['PowerUp'], self.tester.ut_steps)
