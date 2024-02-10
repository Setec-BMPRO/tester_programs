#!/usr/bin/env python3
"""UnitTest for C15A-15 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import c15a15


class C15A15Initial(ProgramTestCase):

    """C15A-15 Initial program test suite."""

    prog_class = c15a15.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Power90": (
                    (sen["vin"], 90.0),
                    (sen["vbus"], 130),
                    (sen["vcc"], 9),
                    (sen["vout"], 15.5),
                    (sen["green"], 11),
                    (sen["yellow"], 0.2),
                ),
                "Power240": (
                    (sen["vin"], 240.0),
                    (sen["vbus"], 340),
                    (sen["vcc"], 12),
                    (sen["vout"], 15.5),
                    (sen["green"], 11),
                    (sen["yellow"], 0.2),
                ),
                "OCP": (
                    (
                        sen["vout"],
                        (15.5,) * 15 + (13.5,),
                    ),
                    (sen["yellow"], 8),
                    (sen["green"], 9),
                    (sen["vout"], (10, 15.5)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(
            ["Power90", "Power240", "OCP", "PowerOff"], self.tester.ut_steps
        )
