#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15 Initial Test program."""

from unittest.mock import MagicMock, patch
from .data_feed import UnitTester, ProgramTestCase
from programs import bc15


class BC15Initial(ProgramTestCase):

    """BC15 Initial program test suite."""

    prog_class = bc15.Initial
    parameter = None
    debug = False
    startup_banner = (
        'BC15\r\n'                          # BEGIN Startup messages
        'Build date:       06/11/2015\r\n'
        'Build time:       15:31:40\r\n'
        'SystemCoreClock:  48000000\r\n'
        'Software version: 1.2.3.456\r\n'
        'nonvol: reading crc invalid at sector 14 offset 0\r\n'
        'nonvol: reading nonvol2 OK at sector 15 offset 2304\r\n'
        'Hardware version: 0.0.[00]\r\n'
        'Serial number:    A9999999999\r\n'
        'Please type help command.'         # END Startup messages
        )

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['bc15_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect':
                    ((sen['olock'], 0.0), (sen['ofanshort'], 3300.0), ),
                'PowerUp':
                    ((sen['oACin'], 240.0), (sen['oVbus'], 330.0),
                     (sen['o12Vs'], 12.0), (sen['o3V3'], 3.3),
                     (sen['o15Vs'], 15.0), (sen['oVout'], 0.2), ),
                'Output': ((sen['oVout'], 14.40), (sen['oVout'], 14.40), ),
                'Loaded': ((sen['oVout'], (14.4, ) * 5 + (11.0, ), ), ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise': (
                    (self.startup_banner, ) +
                    ('OK', ) * 3 +
                    ('{}'.format(bc15.initial.BIN_VERSION), )
                    ),
                'PowerUp': (
                    (self.startup_banner, ) +
                    ('', ) * 10
                    ),
                'Output':
                    ('not-pulsing-volts=14432 ;mV \r\n'
                        'not-pulsing-current=1987 ;mA ',
                    '3',
                    'mv-set=14400 ;mV \r\n'
                        'not-pulsing-volts=14432 ;mV ',
                    'set_volts_mv_num                        902 \r\n'
                        'set_volts_mv_den                      14400 ', ) +
                    ('', ) * 3,
                'Loaded':
                    ('not-pulsing-volts=14432 ;mV \r\n'
                        'not-pulsing-current=14000 ;mA ', ) +
                    ('OK', ) * 2,
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['bc15'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(19, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PartDetect', 'Initialise', 'PowerUp', 'Output', 'Loaded'],
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
                'PartDetect':
                    ((sen['olock'], 0.0), (sen['ofanshort'], 30.0), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(2, len(result.readings))
        self.assertEqual(['PartDetect'], self.tester.ut_steps)