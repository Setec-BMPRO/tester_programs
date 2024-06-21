#!/usr/bin/env python3
"""UnitTest for BCE4/5 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bce4


class _BCE4Final(ProgramTestCase):
    """BCE4/5 Final program base test suite."""

    prog_class = bce4.Final
    parameter = ""

    def _pass_run(self, data):
        """PASS run of the program."""
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(
            ["PowerUp", "FullLoad", "OCP", "LowMains"], self.tester.ut_steps
        )


class BCE4_Final(_BCE4Final):
    """BCE4 Final program test suite."""

    parameter = "4"
    debug = False

    def test_pass_run(self):
        """PASS run of the 12V program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oVout"], (13.6, 13.55)),
                    (sen["oVbat"], 13.3),
                    (sen["oAlarm"], (0.1, 10.0)),
                ),
                "FullLoad": (
                    (sen["oVout"], 13.4),
                    (sen["oVbat"], 13.3),
                ),
                "OCP": (
                    (
                        sen["oVout"],
                        (13.4,) * 15 + (13.0,),
                    ),
                ),
                "LowMains": (
                    (
                        sen["oVout"],
                        (13.4,) * 17 + (13.0,),
                    ),
                ),
            },
        }
        super()._pass_run(data)


class BCE5_Final(_BCE4Final):
    """BCE5 Final program test suite."""

    parameter = "5"
    debug = False

    def test_pass_run(self):
        """PASS run of the 24V program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oVout"], (27.3, 27.2)),
                    (sen["oVbat"], 27.2),
                    (sen["oAlarm"], (0.1, 10.0)),
                ),
                "FullLoad": (
                    (sen["oVout"], 27.2),
                    (sen["oVbat"], 27.1),
                ),
                "OCP": (
                    (
                        sen["oVout"],
                        (27.3,) * 8 + (26.0,),
                    ),
                ),
                "LowMains": (
                    (
                        sen["oVout"],
                        (27.3,) * 17 + (26.0,),
                    ),
                ),
            },
        }
        super()._pass_run(data)
