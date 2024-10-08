#!/usr/bin/env python3
"""UnitTest for 2040 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import _2040


class _2040Final(ProgramTestCase):
    """2040 Final program test suite."""

    prog_class = _2040.Final
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "DCPowerOn": (
                    (sen["o20V"], 20.0),
                    (sen["oYesNoGreen"], True),
                    (sen["o20V"], 20.0),
                ),
                "DCLoad": (
                    (sen["o20V"], 20.0),
                    (sen["oYesNoDCOff"], True),
                ),
                "ACPowerOn": ((sen["o20V"], 20.0),),
                "ACLoad": (
                    (sen["o20V"], 20.0),
                    (sen["oYesNoACOff"], True),
                    (sen["o20V"], 0.0),
                    (sen["oYesNoACOn"], True),
                ),
                "Recover": (
                    (sen["o20V"], 0.0),
                    (sen["o20V"], 20.0),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(12, len(result.readings))
        self.assertEqual(
            ["DCPowerOn", "DCLoad", "ACPowerOn", "ACLoad", "Recover"],
            self.tester.ut_steps,
        )
