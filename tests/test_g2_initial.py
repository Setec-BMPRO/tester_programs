#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GENIUS-II Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import logging
import tester
from . import logging_setup
from .data_feed import DataFeeder
from programs import genius2

_PROG_CLASS = genius2.Initial
_PROG_LIMIT = genius2.INI_LIMIT


class Genius2Initial(unittest.TestCase):

    """GENIUS-II Initial program test suite."""

    @classmethod
    def setUpClass(cls):
        """Per-Class setup. Startup logging."""
        logging_setup()
        # Set lower level logging
        log = logging.getLogger('tester')
        log.setLevel(logging.DEBUG)  # INFO)
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
        sen = self.test_program.sensor
        data = {
            DataFeeder.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen.olock, 0.0), (sen.ovbatctl, 13.0),
                     (sen.ovdd, 5.0), ),
                'Aux': ((sen.ovout, 13.65), (sen.ovaux, 13.70), ),
                'PowerUp':
                    ((sen.oflyld, 30.0), (sen.oacin, 240.0),
                     (sen.ovbus, 330.0), (sen.ovcc, 16.0), (sen.ovbat, 13.0),
                     (sen.ovout, 13.0), (sen.ovdd, 5.0), (sen.ovctl, 12.0), ),
                'VoutAdj':
                    ((sen.oAdjVout, True), (sen.ovout, (13.65, 13.65, )),
                     (sen.ovbatctl, 13.0), (sen.ovbat, 13.65),
                     (sen.ovdd, 5.0), ),
                'ShutDown':
                    ((sen.ofan, (0.0, 13.0)), (sen.ovout, (13.65, 0.0, 13.65)),
                     (sen.ovcc, 0.0), ),
                'OCP':
                    ((sen.ovout, (13.5, ) * 11 + (13.0, ), ),
                     (sen.ovout, (0.1, 13.6, 13.6)),
                     (sen.ovbat, 13.6), ),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(25, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Aux', 'PowerUp', 'VoutAdj', 'ShutDown', 'OCP'],
            self.feeder.steps)

    def test_fail_run(self):
        """FAIL 1st Vout reading."""
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
                    ((sen.olock, 1000), ),
                },
            }
        self.feeder.load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.feeder.result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['Prepare'], self.feeder.steps)
