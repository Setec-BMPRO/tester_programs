#!/usr/bin/env python3
"""UnitTest for BLExtender/SmartLink201 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import smartlink201


class _Initial(ProgramTestCase):

    """Base Initial program test suite."""

    prog_class = smartlink201.Initial

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.BackgroundTimer",
            "share.programmer.ARM",
            "share.bluetooth.SerialToMAC",
            "programs.smartlink201.console.BLExtenderConsole",
            "programs.smartlink201.console.SmartLink201Console",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()


class BLExtenderInitial(_Initial):

    """BLExtender Initial program test suite."""

    parameter = "B"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["SnEntry"], "A2126010123"),
                    (sen["photosense2"], 0.0),
                    (sen["Vbatt"], 12.0),
                    (sen["Vin"], 10.0),
                    (sen["3V3"], 3.3),
                ),
                "PgmNordic": ((sen["JLink"], 0),),
                "Nordic": (
                    (sen["SL_MAC"], "aabbccddeeff"),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(7, len(result.readings))
        self.assertEqual(
            [
                "PowerUp",
                "PgmNordic",
                "Nordic",
            ],
            self.tester.ut_steps,
        )


class SmartLink201Initial(_Initial):

    """SmartLink201 Initial program test suite."""

    parameter = "S"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        sen_tank = []  # Build tank sensor data
        for index in range(16):
            name = smartlink201.console.tank_name(index)
            data = (0xFFF, 0xFFF) if index % 2 else (0xFFF, 0x100)
            sen_tank.append((sen[name], data))
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["SnEntry"], "A2126010123"),
                    (sen["photosense1"], 0.0),
                    (sen["photosense2"], 0.0),
                    (sen["S5tank"], 1.5),
                    (sen["Vbatt"], 12.0),
                    (sen["Vin"], 10.0),
                    (sen["3V3"], 3.3),
                ),
                "PgmNordic": ((sen["JLink"], 0),),
                "Nordic": (
                    (sen["SL_MAC"], "aabbccddeeff"),
                ),
                "Calibrate": (
                    (sen["Vbatt"], 12.01),
                    (
                        sen["SL_Vbatt"],
                        (
                            "12120",
                            "12020",
                        ),
                    ),
                ),
                "TankSense": sen_tank,
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(44, len(result.readings))
        self.assertEqual(
            [
                "PowerUp",
                "PgmARM",
                "PgmNordic",
                "Nordic",
                "Calibrate",
                "TankSense",
            ],
            self.tester.ut_steps,
        )
