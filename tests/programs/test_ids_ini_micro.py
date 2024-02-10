#!/usr/bin/env python3
"""UnitTest for IDS500 Micro Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500MicroInitial(ProgramTestCase):

    """IDS500 Micro Initial program test suite."""

    prog_class = ids500.InitialMicro
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in ("programs.ids500.console.Console",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Program": (
                    (sen["Vsec5VuP"], 5.0),
                    (sen["PicKit"], 0),
                ),
                "Comms": (
                    (sen["SwRev"], ("I,  1, 2,Software Revision",)),
                    (sen["MicroTemp"], ("D, 16,    22,MICRO Temp.(C)",)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(["Program", "Comms"], self.tester.ut_steps)
