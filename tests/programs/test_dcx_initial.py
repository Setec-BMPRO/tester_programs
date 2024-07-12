#!/usr/bin/env python3
"""UnitTest for DCX Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import dcx


class DCX(ProgramTestCase):
    """Initial program test suite."""

    prog_class = dcx.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "programs.dcx.console.Console",
            "share.programmer.ARM",
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
                "Prepare": (
                    (sen["lock"], 10.0),
                    (sen["vbat"], 12.0),
                    (sen["o3v3"], 3.3),
                ),
                "Program": (
                ),
                "Initialise": (
                ),
                "Output": (
                    (sen["vload"], 0.0),
                    (sen["yesnored"], True),
                    (sen["yesnogreen"], True),
                ),
                "RemoteSw": (
                    (sen["vload"], (12.34,)),
                    (sen["arm_remote"], 1),
                ),
                "CanBus": (
                    (sen["canpwr"], 12.5),
                    (sen["arm_canbind"], 1 << 28),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(10, len(result.readings))
        self.assertEqual([
                "Prepare",
                "Program",
                "Initialise",
                "Output",
                "RemoteSw",
                "CanBus",
            ], self.tester.ut_steps)
