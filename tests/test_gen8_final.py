#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GEN8 Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import gen8


class GEN8Final(ProgramTestCase):

    """GEN8 Final program test suite."""

    prog_class = gen8.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['o5v'], 5.1), (sen['o24v'], 0.0), (sen['o12v'], 0.0),
                    (sen['o12v2'], 0.0),
                    ),
                'PowerOn': (
                    (sen['o24v'], 24.0), (sen['o12v'], 12.0),
                    (sen['o12v2'], 0.0), (sen['pwrfail'], 24.1),
                    (sen['o12v2'], 12.0), (sen['yn_mains'], True),
                    (sen['iec'], 240.0),
                    ),
                'FullLoad': (
                    (sen['o5v'], 5.1), (sen['o24v'], 24.1),
                    (sen['o12v'], 12.1), (sen['o12v2'], 12.2),
                    ),
                '115V': (
                    (sen['o5v'], 5.1), (sen['o24v'], 24.1),
                    (sen['o12v'], 12.1), (sen['o12v2'], 12.2),
                    ),
                'Poweroff': (
                    (sen['not_pwroff'], True), (sen['iec'], 0.0),
                    (sen['o24v'], 0.0),
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