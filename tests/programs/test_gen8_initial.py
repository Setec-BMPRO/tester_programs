#!/usr/bin/env python3
"""UnitTest for GEN8 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import gen8


class Gen8Initial(ProgramTestCase):
    """GEN8 Initial program test suite."""

    prog_class = gen8.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "programs.gen8.console.Console",
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
                    (sen["part"], 10.0),
                    (sen["fanshort"], 200.0),
                ),
                "Program": (
                    (sen["o5v"], 5.0),
                    (sen["o3v3"], 3.3),
                ),
                "PowerUp": (
                    (sen["acin"], 240.0),
                    (
                        sen["o5v"],
                        (
                            5.05,
                            5.11,
                        ),
                    ),
                    (sen["o12vpri"], 12.12),
                    (sen["o12v"], 0.12),
                    (
                        sen["o12v2"],
                        (
                            0.12,
                            0.12,
                            12.12,
                        ),
                    ),
                    (
                        sen["o24v"],
                        (
                            0.24,
                            23.23,
                        ),
                    ),
                    (sen["pwrfail"], 0.0),
                    (
                        sen["pfc"],
                        (
                            432.0,
                            432.0,  # Initial reading
                            442.0,
                            442.0,  # After 1st cal
                            440.0,
                            440.0,  # 2nd reading
                            440.0,
                            440.0,  # Final reading
                        ),
                    ),
                    (
                        sen["o12v"],
                        (
                            12.34,
                            12.34,  # Initial reading
                            12.24,
                            12.24,  # After 1st cal
                            12.14,
                            12.14,  # 2nd reading
                            12.18,
                            12.18,  # Final reading
                        ),
                    ),
                    (sen["arm_acfreq"], 50),
                    (sen["arm_acvolt"], 240),
                    (sen["arm_5v"], 5.05),
                    (sen["arm_12v"], 12.180),
                    (sen["arm_24v"], 24.0),
                    (sen["arm_swver"], gen8.initial.Initial.bin_version[:3]),
                    (sen["arm_swbld"], gen8.initial.Initial.bin_version[4:]),
                ),
                "5V": ((sen["o5v"], (5.15, 5.14, 5.10)),),
                "12V": (
                    (sen["o12v"], (12.34, 12.25, 12.00)),
                    (sen["vdsfet"], 0.05),
                ),
                "24V": (
                    (sen["o24v"], (24.33, 24.22, 24.11)),
                    (sen["vdsfet"], 0.05),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(41, len(result.readings))
        self.assertEqual(
            ["PartDetect", "Program", "Initialise", "PowerUp", "5V", "12V", "24V"],
            self.tester.ut_steps,
        )
