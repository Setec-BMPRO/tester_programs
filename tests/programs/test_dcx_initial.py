#!/usr/bin/env python3
"""UnitTest for DCX Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import dcx


@unittest.skip("WIP")
class DCX(ProgramTestCase):
    """Initial program test suite."""

    prog_class = dcx.Initial
    parameter = ""
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mycon = MagicMock(name="MyConsole")
        mycon.ocp_cal.return_value = 1
        patcher = patch("programs.dcx.console.Console", return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_sequence.sensors
        for sensor in sen["arm_loads"]:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["lock"], 10.0),
                    (sen["vbat"], 12.0),
                    (sen["o3v3"], 3.3),
                ),
                "Program": (
                ),
                "Initialise": (
                ),
                "PowerUp": (
                    (sen["o3v3"], 3.3),
                    (
                        sen["o15vs"],
                        (12.5, 14.5),
                    ),
                    (sen["vbat"], 12.8),
                    (
                        sen["arm_vout_ov"],
                        (
                            0,
                            0,
                        ),
                    ),
                ),
                "Output": (
                    (sen["vload"], 0.0),
                    (sen["yesnored"], True),
                    (sen["yesnogreen"], True),
                ),
                "RemoteSw": (
                    (sen["vload"], (12.34,)),
                    (sen["arm_remote"], 1),
                ),
                "CanBus": (
                    (sen["canpwr"], 12.5),
                    (sen["arm_canbind"], 1 << 28),
                ),
            },
            UnitTester.key_call: {  # Callables
                "OCP": (self._arm_loads, 2.0),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(64, len(result.readings))
        self.assertEqual([
                "Prepare",
                "Program",
                "Initialise",
                "SrSolar",
                "Aux",
                "PowerUp",
                "Output",
                "RemoteSw",
                "OCP",
                "CanBus",
            ], self.tester.ut_steps)
