#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import logging
from pydispatch import dispatcher
import tester
from . import logging_setup
from programs import bp35

_PROG_NAME = 'BP35 Initial'
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
        cls._tester = tester.Tester(
            'MockATE', ((_PROG_NAME, _PROG_CLASS, _PROG_LIMIT), ), fifo=True)
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
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.connect(     # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)

    def tearDown(self):
        """Per-Test tear down."""
        dispatcher.disconnect(
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step)
        dispatcher.disconnect(
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result)
        self._tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        cls.patcher.stop()

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
            dev.bp35_ser.flushInput()
            data = self._console_data[stepname]
            for msg in data:
                dev.bp35_puts(msg)
        except KeyError:
            pass
        try:    # Console strings with addprompt=False
            data = self._console_np_data[stepname]
            for msg in data:
                dev.bp35_puts(msg, addprompt=False)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self._result = result

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self._test_program.sensor
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self._test_program.sensor
        # Tuples of sensor data
        self._sensor_data = {
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
            }
        # Callables
        self._callables = {
            'OCP': (self._arm_loads, 2.0),
            }
        # Tuples of console strings
        self._console_data = {
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
                ('0', ),
            'Aux': ('', '13500', '1100', ''),
            'PowerUp':
                ('', ) * 4 +     # Manual mode
                ('0', ) * 2,
            'Output': ('', ) * (1 + 14 + 1),
            'OCP': ('240', '50000', '350', '12800', '500', '', '4000'),
            'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
            }
        # Tuples of strings with addprompt=False
        self._console_np_data = {
            'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
            }
        self._tester.test(('UUT1', ))
        self.assertEqual('P', self._result.code)        # Test Result
        self.assertEqual(68, len(self._result.readings)) # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'SolarReg', 'Aux', 'PowerUp',
             'Output', 'RemoteSw', 'OCP', 'CanBus'],
            self._steps)

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
        sen = self._test_program.sensor
        self._sensor_data = {
            'Prepare':
                ((sen.lock, 10.0), (sen.sernum, ('A1626010123', )),
                 (sen.vbat, 2.5), ),   # Vbat will fail
            }
        self._tester.test(('UUT1', ))
        self.assertEqual(self._result.code, 'F')        # Must have failed
        self.assertEqual(5, len(self._result.readings))
        self.assertEqual(['Prepare'], self._steps)
