#!/usr/bin/env python3
"""UnitTest for MB2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import mb2


class MB2Final(ProgramTestCase):
    """MB2 Final program test suite."""

    prog_class = mb2.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerOn": (
                    (sen["vin"], (12.9, 9.1)),
                    (sen["yesnolight"], True),
                    (sen["vout"], 14.4),
                    (sen["yesnooff"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(
            [
                "PowerOn",
            ],
            self.tester.ut_steps,
        )
