#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35C Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import j35

_PROG_CLASS = j35.Final
_PROG_LIMIT = j35.FIN_LIMIT_C


class J35Final(ProgramTestCase):

    """J35 Final program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT
    parameter = None
    debug = False

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen.vloads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': ((sen.photo, (0.0, 12.0)), ),
                'OCP': ((sen.vload1, (12.7, ) * 10 + (11.0, ), ), ),
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
        self.assertEqual(31, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(['PowerUp', 'Load', 'OCP'], self.tester.ut_steps)
