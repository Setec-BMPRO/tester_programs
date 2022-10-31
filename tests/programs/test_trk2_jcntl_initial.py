#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2/JControl Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2_jcontrol


class _CommonInitial(ProgramTestCase):

    """Trek2/JControl Initial program test suite."""

    prog_class = trek2_jcontrol.Initial
    ser_num = "A1526040123"

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "programs.trek2_jcontrol.console.DirectConsole",
            "programs.trek2_jcontrol.console.TunnelConsole",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["sernum"], (self.ser_num,)),
                    (sen["vin"], (7.0, 12.0)),
                    (sen["3v3"], 3.3),
                ),
                "TestArm": ((sen["swver"], self.test_program.config.sw_version),),
                "CanBus": (
                    (sen["canbind"], 1 << 28),
                    (sen["tunnelswver"], self.test_program.config.sw_version),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(6, len(result.readings))
        self.assertEqual(
            ["PowerUp", "Program", "TestArm", "CanBus"], self.tester.ut_steps
        )


class Trek2Initial(_CommonInitial):

    """Trek2 Initial program test suite."""

    parameter = "TK2"
    debug = False

    def test_pass_run(self):
        """PASS run of the Trek2 program."""
        super()._pass_run()


class JControlInitial(_CommonInitial):

    """JControl Initial program test suite."""

    parameter = "JC"
    debug = False

    def test_pass_run(self):
        """PASS run of the JControl program."""
        super()._pass_run()
