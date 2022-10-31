#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""UnitTest for RVMD50 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmd50


class RVMD50Final(ProgramTestCase):

    """RVMD50 Final program test suite."""

    prog_class = rvmd50.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (),
                "Display": ((sen["YesNoDisplay"], True),),
                "Buttons": (
                    (sen["OkCanButtonPress"], True),
                    (sen["PageButton"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(["PowerUp", "Display", "Buttons"], self.tester.ut_steps)
