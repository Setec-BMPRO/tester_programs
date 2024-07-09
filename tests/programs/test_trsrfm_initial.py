#!/usr/bin/env python3
"""UnitTest for TRS-RFM Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import trsrfm


class TRSRFMInitial(ProgramTestCase):
    """TRS-RFM Initial program test suite."""

    prog_class = trsrfm.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.trsrfm.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["vin"], 12.0),
                    (sen["3v3"], 3.30),
                ),
                "Program": ((sen["JLink"], 0),),
                "Operation": (
                    (
                        sen["red"],
                        (
                            3.1,
                            0.5,
                            3.1,
                        ),
                    ),
                    (
                        sen["green"],
                        (
                            3.1,
                            0.0,
                            3.1,
                        ),
                    ),
                    (
                        sen["blue"],
                        (
                            3.1,
                            0.25,
                            3.1,
                        ),
                    ),
                    (sen["arm_SwVer"], self.test_sequence.sw_version),
                ),
                "Bluetooth": (
                    (sen["BleMac"], "001ec030bc15"),
                    (sen["RSSI"], -50),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(12, len(result.readings))
        self.assertEqual(
            ["Prepare", "Program", "Operation", "Bluetooth"], self.tester.ut_steps
        )
