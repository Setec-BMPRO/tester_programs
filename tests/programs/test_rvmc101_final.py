#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVMC101x Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmc101


class RVMC101Final(ProgramTestCase):

    """RVMC101x Final program test suite."""

    prog_class = rvmc101.Final
    parameter = "FULL"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": ((sen["TabletScreen"], True),),
                "CanBus": (
                    (sen["ButtonPress"], True),
                    (sen["zone4"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(
            tuple("UUT{0}".format(uut) for uut in range(1, self.per_panel + 1))
        )
        for res in self.tester.ut_result:
            self.assertEqual("P", res.code)
            self.assertEqual(3, len(res.readings))
        self.assertEqual(["PowerUp", "CanBus"], self.tester.ut_steps)


class RVMC101FinalLite(ProgramTestCase):

    """RVMC101x Lite Final program test suite."""

    prog_class = rvmc101.Final
    parameter = "LITE"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": ((sen["TabletScreen"], True),),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(
            tuple("UUT{0}".format(uut) for uut in range(1, self.per_panel + 1))
        )
        for res in self.tester.ut_result:
            self.assertEqual("P", res.code)
            self.assertEqual(1, len(res.readings))
        self.assertEqual(["PowerUp"], self.tester.ut_steps)
