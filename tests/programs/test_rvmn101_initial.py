#!/usr/bin/env python3
"""UnitTest for RVMN101 Initial Test program."""

from unittest.mock import MagicMock, PropertyMock, patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmn101


class RVMN101BInitial(ProgramTestCase):
    """RVMN101B Initial program test suite."""

    prog_class = rvmn101.Initial
    parameter = "101B"
    hs_outputs = [1, 2, 3]
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in ("share.bluetooth.SerialToMAC",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mycon = MagicMock(name="MyCon")
        type(mycon).valid_outputs = PropertyMock(return_value=self.hs_outputs)
        patcher = patch("programs.rvmn101.console.Console101B", return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["VBatt"], 12.0),
                    (sen["3V3"], 3.3),
                ),
                "Program": (
                    (sen["JLinkARM"], 0),
                    (sen["JLinkBLE"], 0),
                ),
                "Initialise": ((sen["BleMac"], "aabbccddeeff"),),
                "Input": ((sen["Input"], 0x5A5A),),
                "Output": ((sen["HSout"], 0),),
                "CanBus": ((sen["cantraffic"], True),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(8, len(result.readings))
        self.assertEqual(
            ["PowerUp", "Program", "Initialise", "Input", "Output", "CanBus"],
            self.tester.ut_steps,
        )
