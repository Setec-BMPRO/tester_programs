#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GEN8 Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import gen8

_PROG_CLASS = gen8.Final
_PROG_LIMIT = gen8.FIN_LIMIT


class GEN8Final(ProgramTestCase):

    """GEN8 Final program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen.o5V, 5.1), (sen.o24V, 0.0), (sen.o12V, 0.0),
                    (sen.o12V2, 0.0),
                    ),
                'PowerOn': (
                    (sen.o24V, 24.0), (sen.o12V, 12.0), (sen.o12V2, 0.0),
                    (sen.oPwrFail, 24.1), (sen.o12V2, 12.0),
                    (sen.oYesNoMains, True), (sen.oIec, 240.0),
                    ),
                'FullLoad': (
                    (sen.o5V, 5.1), (sen.o24V, 24.1), (sen.o12V, 12.1),
                    (sen.o12V2, 12.2),
                    ),
                '115V': (
                    (sen.o5V, 5.1), (sen.o24V, 24.1), (sen.o12V, 12.1),
                    (sen.o12V2, 12.2),
                    ),
                'Poweroff': (
                    (sen.oNotifyPwrOff, True), (sen.oIec, 0.0),
                    (sen.o24V, 0.0),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(22, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'PowerOn', 'FullLoad', '115V', 'Poweroff'],
            self.tester.ut_steps)
