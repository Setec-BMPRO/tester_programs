#!/usr/bin/env python3
"""UnitTest for BLE2CAN Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ble2can


class BLE2CANInitial(ProgramTestCase):
    """BLE2CAN Initial program test suite."""

    prog_class = ble2can.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.ble2can.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["tstpin_cover"], 0.0),
                    (sen["vin"], 12.0),
                    (sen["3v3"], 3.30),
                    (sen["5v"], 5.0),
                ),
                "TestArm": (
                    (
                        sen["red"],
                        (
                            3.1,
                            0.5,
                            3.1,
                        ),
                    ),
                    (
                        sen["green"],
                        (
                            3.1,
                            0.0,
                            3.1,
                        ),
                    ),
                    (
                        sen["blue"],
                        (
                            3.1,
                            0.25,
                            3.1,
                        ),
                    ),
                    (sen["SwVer"], self.test_sequence.sw_version),
                ),
                "Bluetooth": ((sen["BtMac"], "00:1E:C0:30:BC:15"),),
                "CanBus": ((sen["CANbind"], 1 << 28),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(16, len(result.readings))
        self.assertEqual(
            ["Prepare", "TestArm", "Bluetooth", "CanBus"], self.tester.ut_steps
        )
