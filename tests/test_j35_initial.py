#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import logging
import tester
from . import logging_setup
from .data_feed import DataFeeder
from programs import j35

_PROG_CLASS = j35.Initial
_PROG_LIMIT = j35.INI_LIMIT


class J35Initial(unittest.TestCase):

    """J35 Initial program test suite."""

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

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.logdev
        dev.j35_ser.flushInput()        # Flush console input buffer
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen.olock, 10.0), (sen.sernum, ('A1626010123', )),
                     (sen.ovbat, 12.5), (sen.oair, 12.5), (sen.o3V3U, 3.3), ),
                'Initialise': ((sen.sernum, ('A1526040123', )), ),
                'Aux': ((sen.oaux, 13.5), (sen.ovbat, 13.5), ),
                'Solar': ((sen.ovbat, 13.5), ),
                'PowerUp':
                    ((sen.oacin, 240.0), (sen.ovbus, 340.0),
                     (sen.o12Vpri, 12.5), (sen.o3V3, 3.3), (sen.o15Vs, 12.5),
                     (sen.ovbat, (12.8, 12.8, )), (sen.ofan, (12, 0, 12)), ),
                'Output': ((sen.ovload, (0.0, ) + (12.8, ) * 14), ),
                'RemoteSw': ((sen.ovload, (0.0, 12.8)), ),
                'Load': ((sen.ovbat, 12.8), ),
                'OCP': ((sen.ovbat, (12.8, ) * 7 + (11.0, ), ), ),
                'CanBus': ((sen.ocanpwr, 12.5), ),
                },
            DataFeeder.key_call: {      # Callables
                'Load': (self._arm_loads, 2.0),
                },
            DataFeeder.key_con: {       # Tuples of console strings
                'Initialise':
                    ('Banner1\r\nBanner2', ) +
                     ('', ) + ('success', ) * 2 + ('', ) +
                     ('Banner1\r\nBanner2', ) +
                     ('', ) + (j35.initial.limit.ARM_VERSION, ),
                'Aux': ('', '13500', '1100', ''),
                'Solar': ('', ''),
                'PowerUp':
                    ('', ) * 5 +     # Manual mode
                    ('0', '', '0', '0', '240', '50000',
                     '350', '12800', '500', '', ),
                'Output': ('', ) * (1 + 14 + 1),
                'Load': ('4000', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            DataFeeder.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,36,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push, dev.j35_puts)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(64, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'Aux', 'Solar', 'PowerUp',
             'Output', 'RemoteSw', 'Load', 'OCP', 'CanBus'],
            self.feeder.steps)

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
            DataFeeder.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen.olock, 10.0), (sen.sernum, ('A1626010123', )),
                     (sen.ovbat, 2.5), ),   # Vbat will fail
                },
            }
        self.feeder.load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('F', result.code)          # Must have failed
        self.assertEqual(3, len(result.readings))
        self.assertEqual(['Prepare'], self.feeder.steps)
