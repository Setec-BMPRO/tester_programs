#!/usr/bin/env python3
"""UnitTest for ACMON Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import acmon


class ACMONInitial(ProgramTestCase):
    """ACMON Initial program test suite."""

    prog_class = acmon.Initial
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["lock"], 50),
                    (sen["vin"], 11.5),
                    (sen["3v3"], 3.3),
                ),
                "Program": ((sen["JLink"], 0),),
                "Run": (
                    (sen["vac1"], 110),
                    (sen["vac2"], 110),
                    (sen["current1"], 25),
                    (sen["current2"], 25),
                    (sen["frequency1"], 50),
                    (sen["frequency2"], 50),
                    (sen["phase1"], 2),
                    (sen["phase2"], 2),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(12, len(result.readings))
        self.assertEqual(["PowerUp", "Program", "Run"], self.tester.ut_steps)
