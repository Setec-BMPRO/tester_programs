#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for MB2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import mb2


class MB2Final(ProgramTestCase):

    """MB2 Final program test suite."""

    prog_class = mb2.Final
    parameter = None
    debug = True

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerOn': (
                    (sen['vout'], 14.0), (sen['yesnogreen'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(2, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerOn', ],
            self.tester.ut_steps)