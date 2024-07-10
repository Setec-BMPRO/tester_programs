#!/usr/bin/env python3
"""UnitTest for BC60 Initial Test program."""

import unittest
from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc60


@unittest.skip("WIP")
class BC60_Initial(ProgramTestCase):
    """Initial program test suite."""

    prog_class = bc60.Initial
    parameter = ""
    vout = 13.8
    inocp = 12.9
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.bc60.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["lock"], 10.0),
                    (sen["vcc_bias"], 15.0),
                ),
                "PowerUp": (
                    (sen["vac"], 240.0),
                    (sen["vbus"], 340.0),
                    (sen["vcc_pri"], 15.5),
                    (sen["vcc_bias"], 15.0),
                    (sen["vbat"], 0.0),
                    (sen["alarm"], 2200),
                ),
                "Calibration": (
                    (sen["vout"], (self.vout,) * 4),
                    (
                        sen["msp_stat"],
                        (
                            0,
                            0,
                        ),
                    ),
                    (sen["msp_vo"], self.vout),
                ),
                "OCP": (
                    (sen["alarm"], 12000),
                    (
                        sen["vout"],
                        (self.vout,) * 15 + (self.inocp,),
                    ),
                    (
                        sen["vbat"],
                        (self.vout,) * 15 + (self.inocp,),
                    ),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(16, len(result.readings))
        self.assertEqual(
            ["Prepare", "Program", "PowerUp", "Calibration", "OCP"],
            self.tester.ut_steps,
        )
