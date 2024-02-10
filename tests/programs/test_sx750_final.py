#!/usr/bin/env python3
"""UnitTest for SX750 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase

from programs import sx750


class SX750Final(ProgramTestCase):

    """SX750 Final program test suite."""

    prog_class = sx750.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "InputRes": ((sen["oInpRes"], 70000),),
                "PowerUp": (
                    (sen["oIec"], (0.0, 240.0)),
                    (sen["o5v"], 5.1),
                    (sen["o12v"], 0.0),
                    (sen["oYesNoGreen"], True),
                ),
                "PowerOn": (
                    (sen["oYesNoBlue"], True),
                    (sen["o5v"], 5.1),
                    (sen["oPwrGood"], 0.1),
                    (sen["oAcFail"], 5.1),
                ),
                "Load": (
                    (sen["o5v"], 5.1),
                    (sen["o12v"], (12.2, 12.1)),
                    (sen["o24v"], (24.2, 24.1)),
                    (sen["oPwrGood"], 0.1),
                    (sen["oAcFail"], 5.1),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(19, len(result.readings))
        self.assertEqual(
            ["InputRes", "PowerUp", "PowerOn", "Load"], self.tester.ut_steps
        )
