#!/usr/bin/env python3
"""UnitTest for IDS500 Bias Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialBias(ProgramTestCase):
    """IDS500 Bias Initial program test suite."""

    prog_class = ids500.InitialBias
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["lock"], 0.0),
                    (sen["400V"], 400.0),
                    (sen["Vcc"], 14.0),
                ),
                "Load": ((sen["12V"], (13.0, 12.8)),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(["PowerUp", "Load"], self.tester.ut_steps)
