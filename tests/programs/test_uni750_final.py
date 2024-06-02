#!/usr/bin/env python3
"""UnitTest for UNI-750 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import uni750


class UNI750Final(ProgramTestCase):
    """UNI-750 Final program test suite."""

    prog_class = uni750.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (
                        (sen["oAcUnsw"], 240.0),
                        (sen["oAcSw"], 0.0),
                    )
                ),
                "PowerOn": (
                    (
                        (sen["oAcSw"], 240.0),
                        (sen["oYesNoFan"], True),
                        (sen["o24V"], 24.5),
                        (sen["o15V"], 15.0),
                        (sen["o12V"], 12.0),
                        (sen["o5V"], 5.1),
                        (sen["o3V3"], 3.3),
                        (sen["o5Vi"], 5.2),
                        (sen["oPGood"], 5.2),
                    )
                ),
                "FullLoad": (
                    (
                        (sen["o24V"], 24.0),
                        (sen["o15V"], 15.0),
                        (sen["o12V"], 12.0),
                        (sen["o5V"], 5.1),
                        (sen["o3V3"], 3.3),
                        (sen["o5Vi"], 5.15),
                        (sen["oPGood"], 5.2),
                    )
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(["PowerUp", "PowerOn", "FullLoad"], self.tester.ut_steps)
