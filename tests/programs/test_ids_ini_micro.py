#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Micro Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500MicroInitial(ProgramTestCase):

    """IDS500 Micro Initial program test suite."""

    prog_class = ids500.InitialMicro
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.ProgramPIC')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['pic'].port.flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Program': (
                    (sen['Vsec5VuP'], 5.0),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Comms': (
                    '',
                    'M,1,Incorrectformat!Type?.?forhelp',
                    'M,3,UnknownCommand!Type?.?forhelp',
                    '2',
                    'MICRO Temp',
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['pic'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(['Program', 'Comms'], self.tester.ut_steps)
