#!/usr/bin/env python3
"""UnitTest for RvView/JDisplay Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvview_jdisplay


class _CommonInitial(ProgramTestCase):
    """RvView/JDisplay Initial program test suite."""

    prog_class = rvview_jdisplay.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "programs.rvview_jdisplay.console.Console",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["vin"], 7.5),
                    (sen["3v3"], 3.3),
                ),
                "Display": (
                    (sen["oYesNoOn"], True),
                    (sen["oYesNoOff"], True),
                    (sen["bklght"], (3.0, 0.0)),
                ),
                "CanBus": ((sen["canbind"], 1 << 28),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(7, len(result.readings))
        self.assertEqual(
            ["PowerUp", "Program", "Initialise", "Display", "CanBus"],
            self.tester.ut_steps,
        )


class RvViewInitial(_CommonInitial):
    """RvView Initial program test suite."""

    parameter = "RV"
    debug = False

    def test_pass_run(self):
        """PASS run of the RvView program."""
        super()._pass_run()


class JDisplayInitial(_CommonInitial):
    """JDisplay Initial program test suite."""

    parameter = "JD"
    debug = False

    def test_pass_run(self):
        """PASS run of the JDisplay program."""
        super()._pass_run()
