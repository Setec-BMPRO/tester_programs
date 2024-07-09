#!/usr/bin/env python3
"""UnitTest for SmartLink201 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import smartlink201


class SmartLink201Final(ProgramTestCase):
    """SmartLink201 Final program test suite."""

    prog_class = smartlink201.Final
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Bluetooth": (
                    (sen["RSSI"], -50),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(["Bluetooth"], self.tester.ut_steps)
