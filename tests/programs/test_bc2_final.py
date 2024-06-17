#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""UnitTest for BC2 Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class _BC2Final(ProgramTestCase):
    """BC2 Final program test suite."""

    prog_class = bc2.Final

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.bc2.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch("share.bluetooth.RaspberryBluetooth")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["vin"], 15.0),
                ),
                "Bluetooth": ((sen["arm_swver"], self.test_sequence.cfg.sw_version),),
                "Calibrate": (
                    (sen["vin"], (14.9999, 15.0)),
                    (sen["arm_Ibatt"], 10.0),
                    (sen["arm_ShuntRes"], self.shunt_res),
                    (sen["arm_query_last"], "cal success:"),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(["Prepare", "Bluetooth", "Calibrate"], self.tester.ut_steps)


class BC2_Final(_BC2Final):
    """BC2 Final program test suite."""

    parameter = "100"
    shunt_res = 800000
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2 program."""
        super()._pass_run()


class BC2H_Final(_BC2Final):
    """BC2H Final program test suite."""

    parameter = "300"
    shunt_res = 90000
    debug = False

    def test_pass_run(self):
        """PASS run of the BC2H program."""
        super()._pass_run()
