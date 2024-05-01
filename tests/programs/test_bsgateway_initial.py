#!/usr/bin/env python3
"""UnitTest for BSGateway Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import bsgateway


class BSGatewayInitial(ProgramTestCase):

    """BSGateway Initial program test suite."""

    prog_class = bsgateway.Initial
    parameter = None
    debug = True

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.bsgateway.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["dev_3v3"], 3.3),
                    (sen["can_3v3"], 3.3),
                ),
                "Program": (
                    (sen["JLink"], 0),
                ),
                "Calibrate": (
                    (sen["dev_3v3"], 3.3),
                ),
                "CanBus": (),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(
            ["PowerUp", "Program", "Calibrate", "CanBus"], self.tester.ut_steps)
