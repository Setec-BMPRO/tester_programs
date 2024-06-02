#!/usr/bin/env python3
"""UnitTest for CN101 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import cn101


class CN101Initial(ProgramTestCase):
    """CN101 Initial program test suite."""

    prog_class = cn101.Initial
    parameter = None
    debug = False
    btmac = "001EC030BC15"

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "share.programmer.ARM",
            "share.bluetooth.RaspberryBluetooth",
            "programs.cn101.console.DirectConsole",
            "programs.cn101.console.TunnelConsole",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PartCheck": (
                    (sen["microsw"], 10.0),
                    (sen["sw1"], 10.0),
                    (sen["sw2"], 10.0),
                ),
                "PowerUp": (
                    (sen["oVin"], 8.0),
                    (sen["o3V3"], 3.3),
                ),
                "TestArm": ((sen["oSwVer"], cn101.config.CN101.sw_version),),
                "TankSense": (
                    (sen["tank1"], 5),
                    (sen["tank2"], 5),
                    (sen["tank3"], 5),
                    (sen["tank4"], 5),
                ),
                "Bluetooth": ((sen["oBtMac"], self.btmac),),
                "CanBus": (
                    (sen["oCANBIND"], 1 << 28),
                    (sen["TunnelSwVer"], cn101.config.CN101.sw_version),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(14, len(result.readings))
        self.assertEqual(
            [
                "PartCheck",
                "PowerUp",
                "Program",
                "TestArm",
                "TankSense",
                "Bluetooth",
                "CanBus",
            ],
            self.tester.ut_steps,
        )
