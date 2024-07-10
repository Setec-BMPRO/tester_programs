#!/usr/bin/env python3
"""UnitTest for BC60 Final Test program."""

import unittest

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc60


@unittest.skip("WIP")
class BC60_Final(ProgramTestCase):
    """Final program test suite."""

    prog_class = bc60.Final
    parameter = ""
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["Alarm"], (10, 10000)),
                    (sen["Vout"], (13.6, 13.55)),
                    (sen["Vbat"], 13.3),
                ),
                "FullLoad": (
                    (sen["YesNoGreen"], True),
                    (sen["Vout"], 13.4),
                    (sen["Vbat"], 13.3),
                ),
                "OCP": (
                    (sen["Vout"], (13.4,) * 15 + (11.0,)),
                    (sen["Vbat"], (13.4,) * 15 + (11.0,)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(["PowerUp", "FullLoad", "OCP"], self.tester.ut_steps)
