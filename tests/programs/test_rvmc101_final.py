#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMC101x Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmc101


class RVMC101Final(ProgramTestCase):

    """RVMC101x Final program test suite."""

    prog_class = rvmc101.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Display': (
                    (sen['yesnodisplay'], True),
                    ),
                'CanBus': (
                    (sen['MirCAN'], True),
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
        self.assertEqual(
            ['PowerUp', 'Display', 'CanBus'],
            self.tester.ut_steps)
