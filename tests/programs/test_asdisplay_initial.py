#!/usr/bin/env python3
"""UnitTest for AsDisplay Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import asdisplay


class ASDisplayInitial(ProgramTestCase):
    """ASDisplay Initial program test suite."""

    prog_class = asdisplay.Initial
    debug = False

    def setUp(self):
        for target in (
            "share.programmer.ARM",
            "programs.asdisplay.console.Console",
            "tester.CANReader",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass(self):
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {
                "PowerUp": (
                    (sen["Vin"], 12.0),
                    (sen["3V3"], 3.3),
                    (sen["5V"], 5.0),
                ),
                "Testmode": ((sen["test_mode"], "OK"),),
                "LEDCheck": (
                    (sen["leds_on"], "OK"),
                    (sen["LEDsOnCheck"], True),
                    (sen["leds_off"], "OK"),
                ),
                "TankSense": (
                    (
                        sen["tank_sensor"],
                        (
                            (0,) * 4,
                            (1,) * 4,
                            (2,) * 4,
                            (3,) * 4,
                            (4,) * 4,
                        ),
                    ),
                ),
                "CanBus": (),
            }
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(28, len(result.readings))
        self.assertEqual(
            ["PowerUp", "PgmARM", "Testmode", "LEDCheck", "TankSense", "CanBus"],
            self.tester.ut_steps,
        )
