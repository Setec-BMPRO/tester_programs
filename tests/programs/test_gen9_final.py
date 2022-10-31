#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GEN9-540 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import gen9


class GEN9Final(ProgramTestCase):

    """GEN9-540 Final program test suite."""

    prog_class = gen9.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["airflow"], 0.0),
                    (sen["o5v"], 5.0),
                    (sen["o12v"], 0.0),
                    (sen["o24v"], 0.0),
                    (sen["pwrfail"], 0.0),
                ),
                "PowerOn": (
                    (sen["airflow"], 12.0),
                    (sen["o12v"], 12.0),
                    (sen["o24v"], 24.0),
                    (sen["pwrfail"], 12.0),
                    (sen["gpo1"], 240.0),
                    (sen["gpo2"], 240.0),
                ),
                "Transient": ((sen["12V_Vmax"], ((0.01,),)),),
                "FullLoad": (
                    (sen["o5v"], 5.0),
                    (sen["o12v"], 12.0),
                    (sen["o24v"], 24.0),
                ),
                "115V": (
                    (sen["o5v"], 5.1),
                    (sen["o24v"], 24.1),
                    (sen["o12v"], 12.1),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(
            ["PowerUp", "PowerOn", "Transient", "FullLoad", "115V"],
            self.tester.ut_steps,
        )
