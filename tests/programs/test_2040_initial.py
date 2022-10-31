#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for 2040 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import _2040


class _2040Initial(ProgramTestCase):

    """2040 Initial program test suite."""

    prog_class = _2040.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "FixtureLock": ((sen["oLock"], 10.0),),
                "SecCheck": (
                    (sen["oVout"], 20.0),
                    (sen["oSD"], 20.0),
                    (sen["oGreen"], 17.0),
                ),
                "DCPowerOn": (
                    (sen["oDCin"], (10.0, 40.0, 25.0)),
                    (sen["oGreen"], 17.0),
                    (sen["oRedDC"], (12.0, 2.5)),
                    (sen["oVccDC"], (12.0,) * 3),
                    (
                        sen["oVout"],
                        (20.0,) * 15 + (18.0,),
                    ),
                    (sen["oSD"], 4.0),
                ),
                "ACPowerOn": (
                    (sen["oACin"], (90.0, 265.0, 240.0)),
                    (sen["oGreen"], 17.0),
                    (sen["oRedAC"], 12.0),
                    (sen["oVbus"], (130.0, 340)),
                    (sen["oVccAC"], (13.0,) * 3),
                    (
                        sen["oVout"],
                        (20.0,) * 15 + (18.0,),
                    ),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(33, len(result.readings))
        self.assertEqual(
            ["FixtureLock", "SecCheck", "DCPowerOn", "ACPowerOn"], self.tester.ut_steps
        )
