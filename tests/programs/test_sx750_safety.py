#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SX750 Safety Test program."""

import unittest

from ..data_feed import UnitTester, ProgramTestCase

from programs import sx750


@unittest.skip("acw sensor read is broken")
class SX750Safety(ProgramTestCase):

    """SX750 Safety program test suite."""

    prog_class = sx750.Safety
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Gnd1": (((sen["gnd1"], 40),)),
                "Gnd2": (((sen["gnd2"], 50),)),
                "Gnd3": (((sen["gnd3"], 60),)),
                "HiPot": (((sen["acw"], (0, 3.0)),)),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(["Gnd1", "Gnd2", "Gnd3", "HiPot"], self.tester.ut_steps)
