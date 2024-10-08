#!/usr/bin/env python3
"""UnitTest for C45A-15 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import c45a15


class C15A15Final(ProgramTestCase):
    """C45A-15 Final program test suite."""

    prog_class = c45a15.Final
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oVout"], 9.0),
                    (sen["oYesNoGreen"], True),
                ),
                "ConnectCMR": (
                    (sen["oYesNoYellow"], True),
                    (sen["oVout"], 16.0),
                    (sen["oYesNoRed"], True),
                ),
                "Load": (
                    (sen["oVout"], 16.0),
                    (sen["oVout"], 16.0),
                    (sen["oVout"], 0.0),
                ),
                "Restart": ((sen["oVout"], 9.0),),
                "Poweroff": (
                    (sen["oVout"], 0.0),
                    (sen["oNotifyOff"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(11, len(result.readings))
        self.assertEqual(
            ["PowerUp", "ConnectCMR", "Load", "Restart", "Poweroff"],
            self.tester.ut_steps,
        )
