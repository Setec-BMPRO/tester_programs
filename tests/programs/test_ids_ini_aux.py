#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Aux Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialAux(ProgramTestCase):

    """IDS500 Aux Initial program test suite."""

    prog_class = ids500.InitialAux
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["olock"], 0.0),
                    (sen["o20VL"], 21.0),
                    (sen["o_20V"], -21.0),
                    (sen["o5V"], 0.0),
                    (sen["o15V"], 15.0),
                    (sen["o_15V"], -15.0),
                    (sen["o15Vp"], 0.0),
                    (sen["o15VpSw"], 0.0),
                    (sen["oPwrGood"], 0.0),
                ),
                "KeySwitch": (
                    (sen["o5V"], 5.0),
                    (sen["o15V"], 15.0),
                    (sen["o_15V"], -15.0),
                    (sen["o15Vp"], 15.0),
                    (sen["o15VpSw"], (0.0, 15.0)),
                    (sen["oPwrGood"], 5.0),
                ),
                "ACurrent": (
                    (sen["oACurr5V"], (0.0, 2.0, 2.0)),
                    (sen["oACurr15V"], (0.1, 0.1, 1.3)),
                ),
                "OCP": (
                    (
                        sen["o5V"],
                        (5.0,) * 20 + (4.7,),
                    ),
                    (
                        sen["o15Vp"],
                        (15.0,) * 30 + (14.1,),
                    ),
                    (sen["oAuxTemp"], 3.5),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(27, len(result.readings))
        self.assertEqual(
            ["PowerUp", "KeySwitch", "ACurrent", "OCP"], self.tester.ut_steps
        )
