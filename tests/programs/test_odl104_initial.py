#!/usr/bin/env python3
"""UnitTest for ODL104 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import odl104


class ODL104Initial(ProgramTestCase):

    """ODL104 Initial program test suite."""

    prog_class = odl104.Initial
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "programs.odl104.console.Console",
            "share.bluetooth.SerialToMAC",
            "tester.CANReader",
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
                    (sen["oSnEntry"], "A2226010123"),
                    (sen["oVin"], 8.0),
                    (sen["o3V3"], 3.3),
                ),
                "Program": ((sen["JLink"], 0),),
                "Nordic": (
                    (sen["o3V3"], 3.3),
                    (sen["BleMac"], "aabbccddeeff"),
                ),
                "TankSense": (
                    (sen["tank1"], 4),
                    (sen["tank2"], 4),
                    (sen["tank3"], 4),
                    (sen["tank4"], 4),
                ),
                "CanBus": (),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(
            ["PartCheck", "PowerUp", "Program", "Nordic", "TankSense", "CanBus"],
            self.tester.ut_steps,
        )
