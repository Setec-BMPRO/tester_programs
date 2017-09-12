#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for 2040 Final Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import _2040


class _2040Final(ProgramTestCase):

    """2040 Final program test suite."""

    prog_class = _2040.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'DCPowerOn':
                    ((sen['o20V'], 20.0), (sen['oYesNoGreen'], True),
                     (sen['o20V'], 20.0), ),
                'DCLoad':
                    ((sen['o20V'], 20.0), (sen['oYesNoDCOff'], True), ),
                'ACPowerOn':
                    ((sen['o20V'], 20.0), ),
                'ACLoad':
                    ((sen['o20V'], 20.0), (sen['oYesNoACOff'], True),
                     (sen['o20V'], 0.0), (sen['oYesNoACOn'], True), ),
                'Recover':
                    ((sen['o20V'], 0.0), (sen['o20V'], 20.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(12, len(result.readings))
        self.assertEqual(
            ['DCPowerOn', 'DCLoad', 'ACPowerOn', 'ACLoad', 'Recover'],
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
                'DCPowerOn':
                    ((sen['o20V'], 10.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['DCPowerOn'], self.tester.ut_steps)
