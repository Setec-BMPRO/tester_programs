#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15 Final Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bc15


class BC15Final(ProgramTestCase):

    """BC15 Final program test suite."""

    prog_class = bc15.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerOn':
                    ((sen['ps_mode'], True), (sen['vout'], 13.80), ),
                'Load':
                    ((sen['vout'], (14.23, ) + (14.2, ) * 8 + (11.0, )),
                     (sen['ch_mode'], True), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(5, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(['PowerOn', 'Load'], self.tester.ut_steps)

    def test_fail_run(self):
        """FAIL 1st Vbat reading."""
        # Patch threading.Event & threading.Timer to remove delays
        mymock = MagicMock()
        mymock.is_set.return_value = True   # threading.Event.is_set()
        patcher = patch('threading.Event', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('threading.Timer', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerOn':
                    ((sen['ps_mode'], True), (sen['vout'], 3.80), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(2, len(result.readings))
        self.assertEqual(['PowerOn'], self.tester.ut_steps)
