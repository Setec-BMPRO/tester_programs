#!/usr/bin/env python3
"""UnitTest for J35C Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import j35


class _J35Final(ProgramTestCase):
    """J35 Final program base test suite."""

    prog_class = j35.Final
    parameter = None
    vout = 12.7

    def setUp(self):
        """Per-Test setup."""
        for target in (
            "serial.Serial",
            "tester.CANTunnel",
            "programs.j35.console.TunnelConsole",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _dmm_loads(self, value):
        """Fill all DMM Load sensors with a value."""
        sen = self.test_sequence.sensors
        for sensor in sen["vloads"]:
            sensor.store(value)

    def _pass_run(self, rdg_count, steps_run):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["photo"], (0.0, 12.0)),
                ),
                "CAN": ((sen["can12v"], 12.0),),
                "OCP": (
                    (
                        sen["vloads"][0],
                        (self.vout,) * 20 + (11.0,),
                    ),
                ),
                "CanCable": (
                    (sen["notifycable"], True),
                    (sen["can12v"], 0.0),
                ),
            },
            UnitTester.key_call: {  # Callables
                "PowerUp": (self._dmm_loads, self.vout),
                "CAN": (
                    self.test_sequence.sensors["swver"].store,
                    self.test_sequence.cfg.sw_version,
                ),
                "Load": (self._dmm_loads, self.vout),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(rdg_count, len(result.readings))
        self.assertEqual(steps_run, self.tester.ut_steps)


class J35_A_Final(_J35Final):
    """J35-A Final program test suite."""

    parameter = "A"
    debug = False

    def test_pass_run(self):
        """PASS run of the A program."""
        super()._pass_run(21, ["PowerUp", "CAN", "Load", "OCP", "CanCable"])


class J35_B_Final(_J35Final):
    """J35-B Final program test suite."""

    parameter = "B"
    debug = False

    def test_pass_run(self):
        """PASS run of the B program."""
        super()._pass_run(35, ["PowerUp", "CAN", "Load", "OCP", "CanCable"])


class J35_C_Final(J35_B_Final):
    """J35-C Final program test suite."""

    parameter = "C"
    debug = False


class J35_D_Final(J35_B_Final):
    """J35-D Final program test suite."""

    parameter = "D"
    debug = False
    vout = 13.9
