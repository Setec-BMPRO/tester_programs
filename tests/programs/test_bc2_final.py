#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class BC2Final(ProgramTestCase):

    """BC2 Final program test suite."""

    prog_class = bc2.Final
    parameter = None
    debug = True

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
#        dev = self.test_program.devices
#        dev['bc2_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Bluetooth': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['vin'], 12.0),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Bluetooth': ('001EC030BC15', ),
                },
            }
        self.tester.ut_load(
#            data, self.test_program.fifo_push, dev['bc2'].puts)
            data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(4, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Bluetooth', 'Cal'],
            self.tester.ut_steps)