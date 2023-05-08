#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for C15D-15 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import c15d15


class C15D15Final(ProgramTestCase):

    """C15D-15 Final program test suite."""

    prog_class = c15d15.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["oVout"], 15.5),
                    (sen["oYesNoGreen"], True),
                    (sen["oYesNoYellowOff"], True),
                    (sen["oNotifyYellow"], True),
                ),
                "OCP": (
                    (
                        sen["oVout"],
                        (15.5,) * 5 + (13.5,),
                    ),
                    (sen["oYesNoYellowOn"], True),
                    (sen["oVout"], 15.5),
                ),
                "OverLoad": ((sen["oVout"], 4.0),),
                "Recover": ((sen["oVout"], 15.5),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(9, len(result.readings))
        self.assertEqual(
            ["PowerUp", "OCP", "OverLoad", "Recover", "PowerOff"], self.tester.ut_steps
        )
