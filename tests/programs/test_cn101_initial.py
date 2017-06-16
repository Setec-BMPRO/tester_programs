#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CN101 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import cn101


class CN101Initial(ProgramTestCase):

    """CN101 Initial program test suite."""

    prog_class = cn101.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['cn101'].port.flushInput()  # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartCheck':
                    ((sen['microsw'], 10.0), (sen['sw1'], 10.0),
                     (sen['sw2'], 10.0), ),
                'PowerUp':
                    ((sen['oSnEntry'], ('A1526040123', )),
                     (sen['oVin'], 8.0), (sen['o3V3'], 3.3), ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TestArm':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) * 5 +
                    (cn101.initial.ARM_VERSION, ),
                'TankSense': (('', ) + ('5', ) * 4),
                'Bluetooth': ('001EC030BC15', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            UnitTester.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['cn101'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(15, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PartCheck', 'PowerUp', 'TestArm', 'TankSense',
             'Bluetooth', 'CanBus'],
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
                'PartCheck':
                    ((sen['microsw'], 1000.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['PartCheck'], self.tester.ut_steps)
