#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""UnitTest for BC2 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class _BC2Initial(ProgramTestCase):
    """BC2 Initial program test suite."""

    prog_class = bc2.Initial

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.bc2.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["vin"], 15.0),
                    (sen["3v3"], 3.30),
                ),
                "TestArm": ((sen["arm_SwVer"], self.test_sequence.cfg.sw_version),),
                "Calibrate": (
                    (sen["vin"], (14.9999, 15.0)),
                    (sen["mircal"], ("cal success:",) * 2),
                    (sen["arm_Vbatt"], 15.0),
                    (sen["arm_Ibatt"], 0.0),
                    (sen["arm_Ioffset"], -1),
                    (sen["arm_VbattLSB"], 2440),
                ),
                "Bluetooth": (
                    (sen["arm_BtMAC"], "001EC030BC15"),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(11, len(result.readings))
        self.assertEqual(
            ["Prepare", "TestArm", "Calibrate", "Bluetooth"], self.tester.ut_steps
        )


class BC2_Initial(_BC2Initial):
    """BC2 Initial program test suite."""

    parameter = "100"
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2 program."""
        super()._pass_run()


class BC2H_Initial(_BC2Initial):
    """BC2H Initial program test suite."""

    parameter = "300"
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2H program."""
        super()._pass_run()
