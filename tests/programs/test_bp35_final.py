#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""UnitTest for BP35 / BP35-II Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bp35


class BP35Final(ProgramTestCase):
    """BP35 / BP35-II Final program test suite."""

    prog_class = bp35.Final
    parameter = "SR"
    debug = False
    vout = 12.7

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "serial.Serial",
            "tester.CANTunnel",
            "programs.bp35.console.TunnelConsole",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self.test_sequence.sensors
        for sensor in sen["vloads"]:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["photo"], (0.0, 12.0)),
                ),
                "CAN": (
                    (sen["can12v"], 12.0),
                    (sen["arm_swver"], self.test_sequence.cfg.arm_sw_version),
                ),
                "OCP": (
                    (
                        sen["vloads"][0],
                        (self.vout,) * 20 + (11.0,),
                    ),
                ),
                "CanCable": (
                    (sen["notifycable"], True),
                    (sen["can12v"], 0.0),
                ),
            },
            UnitTester.key_call: {  # Callables
                "PowerUp": (self._dmm_loads, self.vout),
                "Load": (self._dmm_loads, self.vout),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(35, len(result.readings))
        self.assertEqual(
            ["PowerUp", "CAN", "Load", "OCP", "CanCable"], self.tester.ut_steps
        )
