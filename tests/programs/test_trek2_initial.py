#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2


class Trek2Initial(ProgramTestCase):

    """Trek2 Initial program test suite."""

    prog_class = trek2.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trek2'].port.flushInput()  # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen['oSnEntry'], ('A1526040123', )),
                    (sen['oVin'], 12.0), (sen['o3V3'], 3.3), ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TestArm':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) + ('success', ) * 2 + ('', ) * 2 +
                    (trek2.initial.BIN_VERSION, ),
                'CanBus':
                    ('0x10000000', '', '0x10000000', '', '', ),
                },
            UnitTester.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,16,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['trek2'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(6, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'TestArm', 'CanBus'], self.tester.ut_steps)
