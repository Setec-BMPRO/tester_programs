#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for C15A-15 Final Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import c15a15


class C15A15Final(ProgramTestCase):

    """C15A-15 Final program test suite."""

    prog_class = c15a15.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen['oVout'], 15.5),
                     (sen['oYesNoGreen'], True),
                     (sen['oYesNoYellowOff'], True),
                     (sen['oNotifyYellow'], True), ),
                'OCP':
                    ((sen['oVout'], (15.5, ) * 5 + (13.5, ), ),
                     (sen['oYesNoYellowOn'], True),
                     (sen['oVout'], 15.5), ),
                'FullLoad':
                    ((sen['oVout'], 4.0),
                    (sen['oVout'], 15.5), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(9, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'OCP', 'FullLoad', 'PowerOff'],
            self.tester.ut_steps)

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
                'PowerUp':
                    ((sen['oVout'], 10.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['PowerUp'], self.tester.ut_steps)
