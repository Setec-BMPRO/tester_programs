#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSFinal(ProgramTestCase):

    """TRS2 Final program test suite."""

    prog_class = trs2.Final
    parameter = None
    debug = True

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trs2'].port.flushInput()   # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['tstpin_cover'], 0.0), (sen['vin'], 12.0),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Bluetooth': ('001EC030BC15', ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['trs2'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Prepare', 'Bluetooth', ], self.tester.ut_steps)
