#!/usr/bin/env python3
"""UnitTest for SX600 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase

from programs import sx600


class SX600Final(ProgramTestCase):
    """SX600 Final program test suite."""

    prog_class = sx600.Final
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oIec"], (0.0, 240.0)),
                    (sen["oFanDet"], 4.0),
                    (sen["o5v"], 5.1),
                    (sen["o12v"], 0.0),
                    (sen["oYesNoGreen"], True),
                ),
                "PowerOn": (
                    (sen["oBrktLeft"], 0.0),
                    (sen["oBrktRight"], 0.0),
                    (sen["oFanDet"], 2.0),
                    (sen["oYesNoBlue"], True),
                    (sen["o5v"], 5.1),
                    (sen["oPwrGood"], 0.1),
                    (sen["oAcFail"], 5.1),
                ),
                "Load": (
                    (sen["o5v"], 5.1),
                    (sen["o12v"], (12.1, 12.0)),
                    (sen["o24v"], (24.1, 24.0)),
                    (sen["oPwrGood"], 0.1),
                    (sen["oAcFail"], 5.1),
                ),
                "Load115": (
                    (sen["o5v"], 5.1),
                    (sen["o12v"], 12.0),
                    (sen["o24v"], 24.0),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(25, len(result.readings))
        self.assertEqual(
            ["PowerUp", "PowerOn", "Load", "Load115"], self.tester.ut_steps
        )
