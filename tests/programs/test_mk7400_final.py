#!/usr/bin/env python3
"""UnitTest for MK7-400-1 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import mk7400


class MK7400Final(ProgramTestCase):

    """MK7-400-1 Final program test suite."""

    prog_class = mk7400.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (
                        (sen["o5V"], 5.1),
                        (sen["o12V"], 0.0),
                        (sen["o24V"], 0.0),
                        (sen["o24V2"], 0.0),
                    )
                ),
                "PowerOn": (
                    (
                        (sen["o12V"], 12.0),
                        (sen["o24V"], 24.0),
                        (sen["o24V2"], 0.0),
                        (sen["oPwrFail"], 24.1),
                        (sen["o24V2"], 24.0),
                        (sen["oYesNoMains"], True),
                        (sen["oAux"], 240.0),
                        (sen["oAuxSw"], 240.0),
                    )
                ),
                "FullLoad": (
                    (
                        (sen["o5V"], 5.1),
                        (sen["o12V"], 12.1),
                        (sen["o24V"], 24.1),
                        (sen["o24V2"], 24.2),
                    )
                ),
                "115V": (
                    (
                        (sen["o5V"], 5.1),
                        (sen["o12V"], 12.1),
                        (sen["o24V"], 24.1),
                        (sen["o24V2"], 24.2),
                    )
                ),
                "Poweroff": (
                    (
                        (sen["oNotifyPwrOff"], True),
                        (sen["oAux"], 0.0),
                        (sen["oAuxSw"], 0.0),
                        (sen["o24V"], 0.0),
                    )
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(24, len(result.readings))
        self.assertEqual(
            ["PowerUp", "PowerOn", "FullLoad", "115V", "Poweroff"], self.tester.ut_steps
        )
