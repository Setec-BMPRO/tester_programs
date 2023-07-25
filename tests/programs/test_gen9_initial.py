#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GEN9-540 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import gen9


class Gen9Initial(ProgramTestCase):

    """GEN9-540 Initial program test suite."""

    prog_class = gen9.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "programs.gen9.console.Console",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PartDetect": (
                    (sen["lock"], 10.0),
                    (sen["fanshort"], 700.0),
                ),
                "Program": (
                    (sen["o3v3"], 3.3),
                    (sen["JLink"], 0),
                    ),
                "PowerUp": (
                    (sen["acin"], 240.0),
                    (
                        sen["o5v"],
                        (
                            5.14,
                            5.11,
                        ),
                    ),
                    (sen["o15vccpri"], 15.0),
                    (sen["o12vpri"], 12.0),
                    (
                        sen["o12v"],
                        (
                            0.0,
                            12.0,
                        ),
                    ),
                    (
                        sen["o24v"],
                        (
                            0.0,
                            24.0,
                        ),
                    ),
                    (sen["pwrfail"], 0.0),
                    (
                        sen["pfc"],
                        (
                            432.0,
                            432.0,  # Initial reading
                            430.0,
                            430.0,  # After 1st cal
                            426.0,
                            426.0,  # 2nd reading
                            426.0,
                            426.0,  # Final reading
                        ),
                    ),
                    (sen["holdup"], ((0.07,),)),
                    (sen["arm_acfreq"], 50),
                    (sen["arm_acvolt"], 240),
                    (sen["arm_5v"], 5.05),
                    (sen["arm_12v"], 12.0),
                    (sen["arm_24v"], 24.0),
                ),
                "5V": ((sen["o5v"], (5.15, 5.14, 5.10)),),
                "12V": ((sen["o12v"], (12.24, 12.15, 12.00)),),
                "24V": ((sen["o24v"], (24.33, 24.22, 24.11)),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(29, len(result.readings))
        self.assertEqual(
            ["PartDetect", "Program", "Initialise", "PowerUp", "5V", "12V", "24V"],
            self.tester.ut_steps,
        )
