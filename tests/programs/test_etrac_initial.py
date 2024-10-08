#!/usr/bin/env python3
"""UnitTest for ETrac-II Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import etrac


class ETracInitial(ProgramTestCase):
    """ETrac-II Initial program test suite."""

    prog_class = etrac.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in ("programs.etrac.arduino.Arduino",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (
                        (sen["oVin"], 13.0),
                        (sen["oVin2"], 12.0),
                        (sen["o5V"], 5.0),
                    )
                ),
                "Program": (((sen["pgmEtrac2"], "OK"),)),
                "Load": (
                    (
                        (sen["o5Vusb"], 5.1),
                        (sen["oVbat"], (8.45, 8.4)),
                    )
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(7, len(result.readings))
        self.assertEqual(["PowerUp", "Program", "Load"], self.tester.ut_steps)
