#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVVIEW Initial Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import rvview


class RvViewInitial(ProgramTestCase):

    """RVVIEW Initial program test suite."""

    prog_class = rvview.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['rvview_ser'].flushInput()  # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen['oSnEntry'], ('A1626010123', )),
                     (sen['oVin'], 7.5),
                     (sen['o3V3'], 3.3), ),
                'Display':
                    ((sen['oYesNoOn'], True),
                     (sen['oYesNoOff'], True),
                     (sen['oBkLght'], (3.0, 0.0)), ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) + ('success', ) * 2 + ('', ) +
                    ('Banner1\r\nBanner2', ) +
                    (rvview.initial.BIN_VERSION, ),
                'Display': ('0x10000000', '', '0x10000000', '', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            UnitTester.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['rvview'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(10, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'Initialise', 'Display', 'CanBus'],
            self.tester.ut_steps)
