#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for 2040 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import _2040


class _2040Initial(ProgramTestCase):

    """2040 Initial program test suite."""

    prog_class = _2040.Initial
    parameter = None
    debug = True # False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock':
                    ((sen['oLock'], 10.0), ),
                'SecCheck':
                    ((sen['oVout'], 20.0), (sen['oSD'], 20.0),
                     (sen['oGreen'], 17.0), ),
                'DCPowerOn':
                    ((sen['oDCin'], (10.0, 40.0, 25.0)),
                     (sen['oGreen'], 17.0), (sen['oRedDC'], (12.0, 2.5)),
                     (sen['oVccDC'], (12.0,) * 3),
                     (sen['oVout'], (20.0, ) * 15 + (18.0, ), ),
                     (sen['oSD'], 4.0), ),
                'ACPowerOn':
                    ((sen['oACin'], (90.0, 265.0, 240.0)),
                     (sen['oGreen'], 17.0), (sen['oRedAC'], 12.0),
                     (sen['oVbus'], (130.0, 340)),
                     (sen['oVccAC'], (13.0,) * 3),
                     (sen['oVout'], (20.0, ) * 15 + (18.0, ), ), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(33, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['FixtureLock', 'SecCheck', 'DCPowerOn', 'ACPowerOn'],
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
                'FixtureLock':
                    ((sen['oLock'], 1000.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['FixtureLock'], self.tester.ut_steps)