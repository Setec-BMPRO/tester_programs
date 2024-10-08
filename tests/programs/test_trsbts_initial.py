#!/usr/bin/env python3
"""UnitTest for TRS-BTS Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTS_Initial(ProgramTestCase):
    """TRS-BTS Initial program test suite."""

    prog_class = trsbts.Initial
    parameter = "BTS"
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.trsbts.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["vbat"], 12.5),
                    (sen["3v3"], 3.30),
                    (sen["chem"], 3.0),
                    (sen["sway-"], 2.0),
                    (sen["sway+"], 1.0),
                    (sen["light"], (0.0, 12.0)),
                    (sen["brake"], (0.0, 12.0)),
                ),
                "PgmNordic": ((sen["JLink"], 0),),
                "Operation": (
                    (sen["red"], (0.0, 1.8, 0.0)),
                    (sen["green"], (0.0, 2.5, 0.0)),
                    (sen["blue"], (0.0, 2.8, 0.0)),
                    (sen["light"], 0.1),
                    (sen["remote"], (11.9, 0.0)),
                ),
                "Calibrate": (
                    (sen["arm_vbatt"], (12.4, 12.1)),
                    (sen["vbat"], (12.0, 12.0)),
                    (sen["arm_vpin"], 0.1),
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
        self.assertEqual(26, len(result.readings))
        self.assertEqual(
            ["Prepare", "PgmNordic", "Operation", "Calibrate", "Bluetooth"],
            self.tester.ut_steps,
        )
