#!/usr/bin/env python3
"""UnitTest for TRS-BTS Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTSFinal(ProgramTestCase):
    """TRS-BTS Final program test suite."""

    prog_class = trsbts.Final
    parameter = "BTS"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Pin": (
                    (sen["vbat"], 12.0),
                    (sen["brake"], (12.0, 0.1)),
                    (sen["pin_in"], True),
                ),
                "Bluetooth": (
                    (sen["mirmac"], "001ec030bc15"),
                    (sen["RSSI"], -50),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(["Pin", "Bluetooth"], self.tester.ut_steps)
