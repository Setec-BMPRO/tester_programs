#!/usr/bin/env python3
"""UnitTest for CN102/3 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import cn102


class CN102Final(ProgramTestCase):
    """CN102/3 Final program test suite."""

    prog_class = cn102.Final
    parameter = "103"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
            "Bluetooth": (
                (sen["mirrssi"], -50),
            ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(["Bluetooth"], self.tester.ut_steps)
