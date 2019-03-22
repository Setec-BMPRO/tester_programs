#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""UnitTest for RM-50-24 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import rm50


class RM5024Final(ProgramTestCase):

    """RM-50-24 Final program test suite."""

    prog_class = rm50.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock': (
                    (sen['Lock'], 1.0),
                    ),
                'DCInputLeakage': (
                    (sen['oRsense'], 1000), (sen['oVsense'], 0.05),
                    ),
                'DCInputTrack': (
                    (sen['o24Vdcin'], (23.6, 24.0)),
                    (sen['o24Vdcout'], 23.65),
                    ),
                'ACInput240V': (
                    (sen['o24V'], (24.0, ) * 2),
                    ),
                'ACInput110V': (
                    (sen['o24V'], (24.0, ) * 2),
                    ),
                'ACInput90V': (
                    (sen['o24V'], (24.0, ) * 4),
                    ),
                'OCP': (
                    (sen['o24V'], (24.0, ) * 16 + (22.5, 0.0), ),
                    ),
                'PowerNoLoad': (
                    (sen['o24V'], 24.0), (sen['oInputPow'], 2.0),
                    ),
                'Efficiency': (
                    (sen['oInputPow'], 59.0), (sen['o24V'], 24.0),
                    (sen['oCurrshunt'], 0.0021),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(24, len(result.readings))
        self.assertEqual(
            ['FixtureLock', 'DCInputLeakage', 'DCInputTrack', 'ACInput240V',
             'ACInput110V', 'ACInput90V', 'OCP', 'PowerNoLoad', 'Efficiency'],
            self.tester.ut_steps)
