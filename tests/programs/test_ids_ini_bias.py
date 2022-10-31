#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Bias Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialBias(ProgramTestCase):

    """IDS500 Bias Initial program test suite."""

    prog_class = ids500.InitialBias
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["olock"], 0.0),
                    (sen["o400V"], 400.0),
                    (sen["oPVcc"], 14.0),
                ),
                "OCP": (
                    (
                        sen["o12Vsbraw"],
                        (13.0,) * 4 + (12.5, 0.0),
                    ),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(["PowerUp", "OCP"], self.tester.ut_steps)
