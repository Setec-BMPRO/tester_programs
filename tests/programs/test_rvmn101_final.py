#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""UnitTest for RVMN101 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmn101


class RVMN101Final(ProgramTestCase):
    """RVMN101 Final program test suite."""

    prog_class = rvmn101.Final
    parameter = "101A"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Bluetooth": (
                    (sen["ble_mac"], "001ec030c2be"),
                    (sen["RSSI"], -50),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(["Bluetooth"], self.tester.ut_steps)
