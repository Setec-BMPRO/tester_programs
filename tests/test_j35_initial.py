#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Initial Test program."""

import unittest
from unittest.mock import patch
from pydispatch import dispatcher

import tester
from . import logging_setup
from programs import j35

_PROG_NAME = 'J35 Initial'
_PROG_CLASS = j35.Initial
_PROG_LIMIT = j35.INI_LIMIT


class J35_Initial_TestCase(unittest.TestCase):

    """J35 Initial program test suite."""

    @classmethod
    def setUpClass(cls):
        """Per-Class setup. Startup logging."""
        logging_setup()
        cls._tester = tester.Tester(
            'MockATE', ((_PROG_NAME, _PROG_CLASS, _PROG_LIMIT), ),
            fifo=True, prog_limits=False)
        cls._program = tester.TestProgram(
            _PROG_NAME, per_panel=1, parameter=None, test_limits=[])

    def setUp(self):
        """Per-Test setup."""
        self._tester.open(self._program)
        self._test_program = self._tester.runner.program
        self._sensor_data = {}
        self._callables = {}
        self._console_data = {}
        self._console_np_data = {}
        self._result = None
        self._steps = []
        dispatcher.connect(     # Subscribe to the TestStep signals
            self._signal_step,
            sender=tester._SIGNAL_SENDER,
            signal=tester.testsequence.SigStep)
        dispatcher.connect(     # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester._SIGNAL_SENDER,
            signal=tester.testsequence.SigResult)
        # Patch time.sleep to remove delays
        patcher = patch('time.sleep')
        self._sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        """Per-Test tear down."""
        dispatcher.disconnect(
            self._signal_step,
            sender=tester._SIGNAL_SENDER,
            signal=tester.testsequence.SigStep)
        dispatcher.disconnect(
            self._signal_result,
            sender=tester._SIGNAL_SENDER,
            signal=tester.testsequence.SigResult)
        self._tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs['name']
        self._steps.append(stepname)
        dev = self._test_program.logdev
        try:    # Sensor data
            data = self._sensor_data[stepname]
            self._test_program.fifo_push(data)
        except KeyError:
            pass
        try:    # Callables
            data, value = self._callables[stepname]
            data(value)
        except KeyError:
            pass
        try:    # Console strings
            data = self._console_data[stepname]
            for msg in data:
                print('Message', msg)
                dev.j35_puts(msg)
        except KeyError:
            pass
        try:    # Console strings with addprompt=False
            data = self._console_np_data[stepname]
            for msg in data:
                dev.j35_puts(msg, addprompt=False)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self._result = result

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self._test_program.sensors
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self._test_program.sensors
        # Tuples of sensor data
        self._sensor_data = {
            'Prepare':
                ((sen.olock, 10.0), (sen.sernum, ('A1626010123', )),
                 (sen.ovbat, 12.5), (sen.o3V3U, 3.3), ),
            'Initialise': ((sen.sernum, ('A1526040123', )), ),
            'Aux': ((sen.oaux, 13.5), (sen.oair, 13.5), ),
            'Solar': ((sen.oair, 13.5), ),
            'PowerUp':
                ((sen.oacin, 240.0), (sen.ovbus, 340.0), (sen.o12Vpri, 12.5),
                 (sen.o3V3, 3.3), (sen.o15Vs, 12.5),
                 (sen.ovbat, (12.8, 12.8, )), (sen.ofan, (0, 12.0)), ),
            'Output': ((sen.ovload, (0.0, ) + (12.8, ) * 14), ),
            'RemoteSw': ((sen.ovload, (0.0, 12.8)), ),
            'Load': ((sen.ovbat, 12.8), ),
            'OCP': ((sen.ovbat, (12.8, ) * 8 + (11.0, ), ), ),
            'CanBus': ((sen.ocanpwr, 12.5), ),
            }
        # Callables
        self._callables = {
            'Load': (self._arm_loads, 2.0),
            }
        # Tuples of console strings
        self._console_data = {
            'Initialise':
                ('Banner1\r\nBanner2', ) +
                 ('', ) + ('success', ) * 2 + ('', ) +
                 ('Banner1\r\nBanner2', ) +
                 ('', ) + ('1.0.13788.904', ),
            'Aux': ('', '13500', '1100', ''),
            'Solar': ('', ''),
            'PowerUp':
                ('', ) * 4 +     # Manual mode
                ('0', '', '0', '0', '240', '50000',
                 '350', '12800', '500', '', ),
            'Output': ('', ) * (1 + 14 + 1),
            'Load': ('4000', ),
            'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
            }
        # Tuples of strings with addprompt=False
        self._console_np_data = {
            'CanBus': ('RRQ,36,0,7,0,0,0,0,0,0,0\r\n', ),
            }
        self._tester.test(('UUT1', ))
        self.assertEqual('P', self._result.code)        # Test Result
        self.assertEqual(63, len(self._result.readings)) # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'Aux', 'Solar', 'PowerUp',
             'Output', 'RemoteSw', 'Load', 'OCP', 'CanBus'],
            self._steps)

    def test_fail_run(self):
        """FAIL 1st Vbat reading."""
        sen = self._test_program.sensors
        self._sensor_data = {
            'Prepare':
                ((sen.olock, 10.0), (sen.sernum, ('A1626010123', )),
                 (sen.ovbat, 2.5), ),   # Vbat will fail
            }
        self._tester.test(('UUT1', ))
        self.assertEqual(self._result.code, 'F')        # Must have failed
        self.assertEqual(3, len(self._result.readings))
        self.assertEqual(['Prepare'], self._steps)
