#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BCE282 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bce282


class _BCE282Final(ProgramTestCase):

    """BCE282 Final program base test suite."""

    prog_class = bce282.Final
    parameter = None

    def _pass_run(self, data):
        """PASS run of the program."""
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(['PowerUp', 'FullLoad', 'OCP'], self.tester.ut_steps)


class BCE282_12_Final(_BCE282Final):

    """BCE282-12 Final program test suite."""

    parameter = '12'
    debug = False

    def test_pass_run(self):
        """PASS run of the 12V program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['Alarm'], (10, 10000)),
                    (sen['Vout'], (13.6, 13.55)),
                    (sen['Vbat'], 13.3),
                    ),
                'FullLoad': (
                    (sen['YesNoGreen'], True),
                    (sen['Vout'], 13.4),
                    (sen['Vbat'], 13.3),
                    ),
                'OCP': (
                    (sen['Vout'], (13.4, ) * 15 + (13.0, ), ),
                    (sen['Vbat'], (13.4, ) * 15 + (13.0, ), ),
                    ),
                },
            }
        super()._pass_run(data)


class BCE282_24_Final(_BCE282Final):

    """BCE282-24 Final program test suite."""

    parameter = '24'
    debug = False

    def test_pass_run(self):
        """PASS run of the 24V program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['Alarm'], (10, 10000)),
                    (sen['Vout'], (27.6, 27.6)),
                    (sen['Vbat'], 27.5),
                    ),
                'FullLoad': (
                    (sen['YesNoGreen'], True),
                    (sen['Vout'], 27.2),
                    (sen['Vbat'], 27.1),
                    ),
                'OCP': (
                    (sen['Vout'], (27.3, ) * 8 + (26.0, ), ),
                    (sen['Vbat'], (27.3, ) * 8 + (26.0, ), ),
                    ),
                },
            }
        super()._pass_run(data)
