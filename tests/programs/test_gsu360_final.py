#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GSU360-1TA Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import gsu360


class GSU3601TAFinal(ProgramTestCase):

    """GSU360-1TA Final program test suite."""

    prog_class = gsu360.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["o24V"], 24.00),
                    (sen["oYesNoGreen"], True),
                ),
                "FullLoad": (
                    (sen["o24V"], 24.10),
                    (sen["o24V"], 24.00),
                ),
                "OCP": (
                    (
                        sen["o24V"],
                        (24.1,) * 15 + (22.0,),
                    ),
                ),
                "Shutdown": ((sen["o24V"], 4.0),),
                "Restart": ((sen["o24V"], 24.0),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(7, len(result.readings))
        self.assertEqual(
            ["PowerUp", "FullLoad", "OCP", "Shutdown", "Restart"], self.tester.ut_steps
        )
