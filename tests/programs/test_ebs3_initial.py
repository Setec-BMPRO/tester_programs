#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for EBS3 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ebs3


class EBS3Initial(ProgramTestCase):

    """EBS3 Initial program test suite."""

    prog_class = ebs3.Initial

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'CapCharge': (
                    (sen['lock'], 0.0),
                    ),
                'GetTube': (
                    (sen['vtube'], ((999.0, 1001.0), )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(
            ['CapCharge', 'GetTube', ], self.tester.ut_steps)


class _6_T2_Initial(EBS3Initial):

    """EBS3-6-T2 Initial program test suite."""

    parameter = '6-T2'
    debug = True

    def test_pass_run(self):
        """PASS run of the EBS3-6-T2 program."""
        super()._pass_run()


class _6_T5_Initial(EBS3Initial):

    """EBS3-6-T5 Initial program test suite."""

    parameter = '6-T5'
    debug = False

    def test_pass_run(self):
        """PASS run of the EBS3-6-T5 program."""
        super()._pass_run()
