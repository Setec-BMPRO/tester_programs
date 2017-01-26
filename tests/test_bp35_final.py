#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""UnitTest for BP35 Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import bp35

_PROG_CLASS = bp35.Final
_PROG_LIMIT = ()


class BP35Final(ProgramTestCase):

    """BP35 Final program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.support.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen.vbat, 12.8),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(1, len(result.readings))   # Reading count
        # And did all steps run in turn?
        self.assertEqual(['PowerUp'], self.tester.ut_steps)
