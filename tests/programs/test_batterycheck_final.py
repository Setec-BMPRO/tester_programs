#!/usr/bin/env python3
"""UnitTest for BatteryCheck Final Test program."""

from unittest.mock import Mock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import batterycheck


class BatteryCheckFinal(ProgramTestCase):
    """BatteryCheck Final program test suite."""

    prog_class = batterycheck.Final
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mybt = Mock(name="MyBtRadio")
        mybt.scan.return_value = True, "1234"
        mybt.jsonrpc.return_value = {
            "SoftwareVersion": batterycheck.Final.arm_version,
            "SerialID": self.uuts[0].sernum,
        }
        patcher = patch(
            "programs.batterycheck.eunistone_pan1322.BtRadio", return_value=mybt
        )
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["o12V"], 12.0),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(5, len(result.readings))
        self.assertEqual(["PowerUp", "TestBlueTooth"], self.tester.ut_steps)
