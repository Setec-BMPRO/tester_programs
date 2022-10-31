#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Drifter(BM) Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import drifter


class _DrifterInitial(ProgramTestCase):

    """Drifter(BM) Initial program test suite."""

    prog_class = drifter.Initial

    def setUp(self):
        """Per-Test setup."""
        for target in ("programs.drifter.console.Console",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oVin"], 12.0),
                    (sen["oVcc"], 3.3),
                ),
                "Program": ((sen["PicKit"], 0),),
                "CalPre": (
                    (sen["oVsw"], 3.3),
                    (sen["oVref"], 3.3),
                    (sen["o3V3"], -2.7),
                    (sen["o0V8"], -0.8),
                    (sen["pic_Status"], 0),
                ),
                "Calibrate": (
                    (sen["oVin"], 12.0),
                    (sen["oIsense"], 0.090),
                    (sen["oVcc"], 3.3),
                    (sen["pic_ZeroChk"], -65),
                    (
                        sen["pic_Vin"],
                        (
                            11.95,
                            11.98,
                        ),
                    ),
                    (
                        sen["pic_isense"],
                        (
                            -89.0,
                            -89.9,
                        ),
                    ),
                    (sen["pic_Vfactor"], 20000),
                    (sen["pic_Ifactor"], 15000),
                    (sen["pic_Ioffset"], -8),
                    (sen["pic_Ithreshold"], 160),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(23, len(result.readings))
        self.assertEqual(
            ["PowerUp", "Program", "CalPre", "Calibrate"], self.tester.ut_steps
        )


class Drifter_Initial(_DrifterInitial):

    """Drifter Initial program test suite."""

    parameter = "STD"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run()


class DrifterBM_Initial(_DrifterInitial):

    """DrifterBM Initial program test suite."""

    parameter = "BM"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run()
