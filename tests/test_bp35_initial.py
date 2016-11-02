#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import logging
import tester
from . import logging_setup
from .data_feed import DataFeeder
from programs import bp35

_PROG_CLASS = bp35.Initial
_PROG_LIMIT = bp35.INI_LIMIT


class BP35Initial(unittest.TestCase):

    """BP35 Initial program test suite."""

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
        sen = self.test_program.sensor
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensor
        dev = self.test_program.logdev
        dev.bp35_ser.flushInput()       # Flush console input buffer
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen.lock, 10.0), (sen.hardware, 1000),
                     (sen.vbat, 12.0), (sen.o3v3, 3.3), (sen.o3v3prog, 3.3),
                     (sen.sernum, ('A1626010123', )), ),
                'Initialise': ((sen.sernum, ('A1526040123', )), ),
                'SolarReg': ((sen.vsreg, (13.0, 13.5)), ),
                'Aux': ((sen.vbat, 13.5), ),
                'PowerUp':
                    ((sen.acin, 240.0), (sen.pri12v, 12.5), (sen.o3v3, 3.3),
                     (sen.o15Vs, 12.5), (sen.vbat, 12.8),
                     (sen.vpfc, (415.0, 415.0), )),
                'Output': ((sen.vload, (0.0, ) + (12.8, ) * 14), ),
                'RemoteSw': ((sen.vload, (0.25, 12.34)), ),
                'OCP':
                    ((sen.fan, (0, 12.0)), (sen.vbat, 12.8),
                     (sen.vbat, (12.8, ) * 6 + (11.0, ), ), ),
                },
            DataFeeder.key_call: {      # Callables
                'OCP': (self._arm_loads, 2.0),
                },
            DataFeeder.key_con: {       # Tuples of console strings
                'Initialise':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) + ('success', ) * 2 + ('', ) * 4 +
                    ('Banner1\r\nBanner2', ) +
                    ('', ) +
                    (bp35.initial.limit.ARM_VERSION, ) +
                    ('', ) + ('0x10000', ) + ('', ) * 3,      # Manual mode
                'SolarReg':
                    ('1.0', '0') +      # Solar alive, Vout OV
                    ('0', ) * 3 +       # 2 x Solar VI, Vout OV
                    ('0', '1') +        # Errorcode, Relay
                    ('0', ) +          # Vcal
                    ('0', ) * 2,
                'Aux': ('', '13500', '1100', ''),
                'PowerUp':
                    ('', ) * 4 +     # Manual mode
                    ('0', ) * 2,
                'Output': ('', ) * (1 + 14 + 1),
                'OCP': ('240', '50000', '350', '12800', '500', '', '4000'),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            DataFeeder.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push, dev.bp35_puts)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(68, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'SolarReg', 'Aux', 'PowerUp',
             'Output', 'RemoteSw', 'OCP', 'CanBus'],
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
        sen = self.test_program.sensor
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen.lock, 10.0), (sen.sernum, ('A1626010123', )),
                     (sen.vbat, 2.5), ),   # Vbat will fail
                },
            }
        self.feeder.load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(5, len(result.readings))
        self.assertEqual(['Prepare'], self.feeder.steps)
