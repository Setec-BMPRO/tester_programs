#!/usr/bin/env python3
"""UnitTest for WTSI200 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import wtsi200


class WTSI200Final(ProgramTestCase):

    """WTSI200 Final program test suite."""

    prog_class = wtsi200.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerOn": ((sen["oTankLevels"], ((3.1, 3.2, 3.3),)),),
                "Tank1": (
                    (
                        sen["oTankLevels"],
                        (
                            (2.4, 3.2, 3.3),
                            (1.7, 3.2, 3.3),
                            (0.2, 3.2, 3.3),
                        ),
                    ),
                ),
                "Tank2": (
                    (
                        sen["oTankLevels"],
                        (
                            (3.1, 2.4, 3.3),
                            (3.1, 1.7, 3.3),
                            (3.1, 0.2, 3.3),
                        ),
                    ),
                ),
                "Tank3": (
                    (
                        sen["oTankLevels"],
                        (
                            (3.1, 3.2, 2.4),
                            (3.1, 3.2, 1.7),
                            (3.1, 3.2, 0.2),
                        ),
                    ),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(30, len(result.readings))
        self.assertEqual(["PowerOn", "Tank1", "Tank2", "Tank3"], self.tester.ut_steps)
