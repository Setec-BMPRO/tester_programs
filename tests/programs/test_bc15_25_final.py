#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15/25 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc15_25


class _BC15_25_Final(ProgramTestCase):

    """BC15/25 Final program test suite."""

    prog_class = bc15_25.Final

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerOn':
                    ((sen['ps_mode'], True), (sen['vout'], 13.80), ),
                'Load':
                    ((sen['vout'], (14.23, ) + (14.2, ) * 8 + (11.0, )),
                     (sen['ch_mode'], True), ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(['PowerOn', 'Load'], self.tester.ut_steps)


class BC15_Final(_BC15_25_Final):

    """BC15 Initial program test suite."""

    parameter = '15'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC15 program."""
        super()._pass_run()


class BC25_Final(_BC15_25_Final):

    """BC25 Initial program test suite."""

    parameter = '25'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC25 program."""
        super()._pass_run()