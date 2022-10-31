#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GENIUS-II(H) Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import genius2


class _Genius2Final(ProgramTestCase):

    """GENIUS-II(H) Final program base test suite."""

    prog_class = genius2.Final
    parameter = None

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PartDetect": (
                    (sen["inres"], 135e3),
                    (sen["dcinshrt"], 10e3),
                ),
                "PowerOn": (
                    (sen["vout"], 13.6),
                    (sen["vbat"], 13.6),
                ),
                "BattFuse": (
                    (sen["yesnofuseout"], True),
                    (sen["vbat"], 0.0),
                    (sen["yesnofusein"], True),
                    (sen["vout"], 13.6),
                ),
                "OCP": (
                    (
                        sen["vout"],
                        (13.5,) * 11 + (13.0,),
                    ),
                    (sen["vout"], (0.1, 13.6, 13.6)),
                    (sen["vbat"], 13.6),
                ),
                "RemoteSw": (
                    (sen["vbat"], 12.0),
                    (sen["vout"], (12.0, 0.0, 12.0)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(17, len(result.readings))
        self.assertEqual(
            ["PartDetect", "PowerOn", "BattFuse", "OCP", "RemoteSw"],
            self.tester.ut_steps,
        )


class Genius2_Std_Final(_Genius2Final):

    """GENIUS-II Final program test suite."""

    parameter = "STD"
    debug = False

    def test_pass_run(self):
        super()._pass_run()


class Genius2_H_Final(_Genius2Final):

    """GENIUS-IIH Final program test suite."""

    parameter = "H"
    debug = False

    def test_pass_run(self):
        super()._pass_run()
