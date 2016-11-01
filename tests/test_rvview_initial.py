#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVVIEW Initial Test program."""

import unittest
from unittest.mock import patch
import logging
import tester
from . import logging_setup
from .data_feed import DataFeeder
from programs import rvview

_PROG_CLASS = rvview.Initial
_PROG_LIMIT = rvview.INI_LIMIT


class RvViewInitial(unittest.TestCase):

    """RVVIEW Initial program test suite."""

    @classmethod
    def setUpClass(cls):
        """Per-Class setup. Startup logging."""
        logging_setup()
        # Set lower level logging
        log = logging.getLogger('tester')
        log.setLevel(logging.INFO)
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        cls.tester = tester.Tester(
            'MockATE', (('ProgName', _PROG_CLASS, _PROG_LIMIT), ), fifo=True)
        cls.program = tester.TestProgram(
            'ProgName', per_panel=1, parameter=None, test_limits=[])
        cls.feeder = DataFeeder()

    def setUp(self):
        """Per-Test setup."""
        self.tester.open(self.program)
        self.test_program = self.tester.runner.program

    def tearDown(self):
        """Per-Test tear down."""
        self.tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        cls.patcher.stop()
        cls.feeder.stop()
        cls.tester.stop()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.logdev
        dev.rvview_ser.flushInput()     # Flush console input buffer
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen.oSnEntry, ('A1626010123', )), (sen.oVin, 7.5),
                     (sen.o3V3, 3.3), ),
                'Display':
                    ((sen.oYesNoOn, True), (sen.oYesNoOff, True),
                     (sen.oBkLght, (3.0, 0.0)), ),
                },
            DataFeeder.key_call: {      # Callables
                },
            DataFeeder.key_con: {       # Tuples of console strings
                'Initialise':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) + ('success', ) * 2 + ('', ) +
                    ('Banner1\r\nBanner2', ) +
                    (rvview.initial.limit.BIN_VERSION, ),
                'Display': ('0x10000000', '', '0x10000000', '', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            DataFeeder.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push, dev.rvview_puts)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(10, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'Initialise', 'Display', 'CanBus'],
            self.feeder.steps)
