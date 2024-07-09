#!/usr/bin/env python3
"""UnitTest for TRS2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSFinal(ProgramTestCase):
    """TRS2 Final program test suite."""

    prog_class = trs2.Final
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["vin"], 12.0),
                ),
                "Bluetooth": (
                    (sen["mirscan"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(
            [
                "Prepare",
                "Bluetooth",
            ],
            self.tester.ut_steps,
        )
