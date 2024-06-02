#!/usr/bin/env python3
"""UnitTest for SX600 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase

from programs import sx600


class SX600Initial(ProgramTestCase):
    """SX600 Initial program test suite."""

    prog_class = sx600.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "programs.sx600.console.Console",
            "programs.sx600.arduino.Arduino",
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
                "Lock": ((sen["Lock"], 10.1),),
                "Program": (
                    (sen["o5Vsb"], 5.0),
                    (sen["o5Vsbunsw"], (5.0,) * 2),
                    (sen["o3V3"], 3.21),
                    (sen["o8V5Ard"], 8.5),
                    (sen["PriCtl"], 12.34),
                    (sen["ocpMax"], "OK"),
                    (sen["JLink"], 0),
                    (sen["o5Vsb"], 5.0),
                    (sen["o5Vsbunsw"], 5.0),
                ),
                "PowerUp": (
                    (sen["ACin"], 240.0),
                    (sen["PriCtl"], 12.34),
                    (sen["o5Vsb"], 5.05),
                    (sen["o12V"], (0.12, 12.01)),
                    (sen["o24V"], (0.24, 24.01)),
                    (sen["ACFAIL"], 5.0),
                    (sen["PGOOD"], 0.123),
                    (
                        sen["PFC"],
                        (
                            435.0,
                            435.0,
                        ),
                    ),
                    (sen["ARM_AcFreq"], 50),
                    (sen["ARM_AcVolt"], 240),
                    (sen["ARM_12V"], 12.180),
                    (sen["ARM_24V"], 24.0),
                ),
                "5Vsb": (
                    (
                        sen["o5Vsb"],
                        (
                            5.20,
                            5.15,
                            5.14,
                            5.10,
                        ),
                    ),
                ),
                "12V": (
                    (
                        sen["o12V"],
                        (
                            12.34,
                            12.25,
                            12.10,
                            12.00,
                            12.34,
                        ),
                    ),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 37 reads before OCP detected
                    (
                        sen["o12VinOCP"],
                        ((0.123,) * 32 + (4.444,)) + ((0.123,) * 37 + (4.444,)),
                    ),
                    (sen["ocp12Unlock"], "OK"),
                    (sen["ocpStepDn"], ("OK",) * 35),
                    (sen["ocpLock"], "OK"),
                ),
                "24V": (
                    (sen["o24V"], (24.44, 24.33, 24.22, 24.11, 24.24)),
                    # OCP CHECK: Push 18 reads before OCP detected
                    (sen["o24VinOCP"], ((0.123,) * 18 + (4.444,))),
                ),
                "PeakPower": (
                    (sen["o5Vsb"], 5.15),
                    (sen["o12V"], 12.22),
                    (sen["o24V"], 24.44),
                    (sen["PGOOD"], 0.15),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(40, len(result.readings))
        self.assertEqual(
            ["Lock", "Program", "PowerUp", "5Vsb", "12V", "24V", "PeakPower"],
            self.tester.ut_steps,
        )
