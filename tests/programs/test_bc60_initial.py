#!/usr/bin/env python3
"""UnitTest for BC60 Initial Test program."""

from unittest.mock import patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc60


class BC60_Initial(ProgramTestCase):
    """Initial program test suite."""

    prog_class = bc60.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.bc60.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["lock"], 10.0),
                    (sen["15Vsb"], 12.5),
                    (sen["5V"], 5.0),
                    (sen["3V3"], 3.3),
                ),
                "Program": (
                    (sen["JLinkBLE"], 0),
                    (sen["JLinkSTM"], 0),
                ),
                "PowerUp": (
                    (sen["Vac"], 240.0),
                    (sen["400V"], (340.0, 425.0)),
                    (sen["12VPri"], 13.5),
                    (sen["12VPri_Relay"], 12.0),
                    (sen["15Vsb"], 12.5),
                    (sen["5V"], 5.0),
                    (sen["3V3"], 3.3),
                    (sen["Vout"], 13.0),
                ),
                "Load": (
                    (sen["Vout"], (13.0, ) * 7),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(22, len(result.readings))
        self.assertEqual(
            ["Prepare", "Program", "PowerUp", "Load"],
            self.tester.ut_steps,
        )
