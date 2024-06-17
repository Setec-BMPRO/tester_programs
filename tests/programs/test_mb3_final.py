#!/usr/bin/env python3
"""UnitTest for MB3 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import mb3


class MB3Final(ProgramTestCase):
    """MB3 Final program test suite."""

    prog_class = mb3.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerOn": (
                    (sen["vaux"], 12.8),
                    (sen["vbat"], 14.6),
                    (sen["vchem"], 2.5),
                ),
                "Solar": (
                    (sen["vsol"], 14.6),
                    (sen["vbat"], (0.0, 14.6)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(["PowerOn", "Solar"], self.tester.ut_steps)
