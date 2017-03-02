#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35C Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import j35

COUNT_A = 7
COUNT_BC = 14


class _J35Final(ProgramTestCase):

    """J35 Final program base test suite."""

    prog_class = j35.Final
    parameter = None

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen['vloads']:
            sensor.store(value)

    def _pass_run(self, rdg_count):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': ((sen['photo'], (0.0, 12.0)), ),
                'OCP': ((sen['vloads'][0], (12.7, ) * 4 + (11.0, ), ), ),
                },
            UnitTester.key_call: {      # Callables
                'PowerUp': (self._dmm_loads, 12.7),
                'Load': (self._dmm_loads, 12.7),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(rdg_count, len(result.readings))
        # And did all steps run in turn?
        self.assertEqual(['PowerUp', 'Load', 'OCP'], self.tester.ut_steps)


class J35_A_Final(_J35Final):

    """J35-A Final program test suite."""

    parameter = 'A'
    debug = False

    def test_pass_run(self):
        super()._pass_run(17)


class J35_B_Final(_J35Final):

    """J35-B Final program test suite."""

    parameter = 'B'
    debug = False

    def test_pass_run(self):
        super()._pass_run(31)


class J35_C_Final(_J35Final):

    """J35-C Final program test suite."""

    parameter = 'C'
    debug = False

    def test_pass_run(self):
        super()._pass_run(31)
