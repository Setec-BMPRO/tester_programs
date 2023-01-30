#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for ACMON Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import acmon


class ACMONInitial(ProgramTestCase):

    """ACMON Initial program test suite."""

    prog_class = acmon.Initial
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["vin"], 11.5),
                    (sen["3v3"], 3.3),
                ),
                "Program": ((sen["JLink"], 0),),
                "Run": (
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(["PowerUp", "Program", "Run"], self.tester.ut_steps)
