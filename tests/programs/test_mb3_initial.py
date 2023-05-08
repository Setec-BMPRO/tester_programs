#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for MB3 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import mb3


class MB3Initial(ProgramTestCase):

    """MB3 Initial program test suite."""

    prog_class = mb3.Initial
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in ("share.programmer.AVR",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerOn": (
                    (sen["vaux"], 12.8),
                    (sen["5V"], 5.0),
                ),
                "Output": ((sen["vbat"], 14.6),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(["PowerOn", "PgmAVR", "Output"], self.tester.ut_steps)
