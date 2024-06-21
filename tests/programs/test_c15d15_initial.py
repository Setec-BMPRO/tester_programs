#!/usr/bin/env python3
"""UnitTest for C15D-15 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import c15d15


class C15D15Initial(ProgramTestCase):
    """C15D-15 Initial program test suite."""

    prog_class = c15d15.Initial
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["vin"], 30.0),
                    (sen["vcc"], 13.0),
                    (sen["vout"], 15.5),
                    (sen["led_green"], 10.0),
                    (sen["led_yellow"], 0.2),
                ),
                "OCP": (
                    (
                        sen["vout"],
                        (15.5,) * 22 + (13.5,),
                    ),
                ),
                "Charging": (
                    (
                        sen["vout"],
                        (
                            13.5,
                            15.5,
                        ),
                    ),
                    (sen["led_green"], 10.0),
                    (sen["led_yellow"], 10.0),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(["PowerUp", "OCP", "Charging"], self.tester.ut_steps)
