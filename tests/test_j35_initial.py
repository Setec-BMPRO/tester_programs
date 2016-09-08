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
        self._fifo_data = {}
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
#        self._test_program.fifo_push(self._fifo_data[stepname])

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        result = kwargs['result']
        self._result = result

    def test_pass_run(self):
        """PASS run of the program."""
#        sen = self._test_program.sensors
#        self._fifo_data = {
#            'Step1': ((sen.oDcVin1, 11.0),
#                     ),
#            'Step2': ((sen.oDcVin1, 11.0),
#                      (sen.oDcVin2, 12.0),
#                     ),
#            'Step3': ((sen.oNotify, True),
#                      (sen.oYesNo, True),
#                      (sen.oOkCan, True),
#                      (sen.oDataEntry, ('Hello World!', )),
#                      (sen.oAdjustAnalog, True),
#                      ),
#            }
        self._tester.test(('UUT1', ))
        self.assertEqual(self._result.code, 'P')        # Must have passed
        self.assertEqual(len(self._result.readings), 63) # Correct # of readings
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'Aux', 'Solar', 'PowerUp',
             'Output', 'RemoteSw', 'Load', 'OCP', 'CanBus'],
            self._steps)

#    def test_fail_run(self):
#        """FAIL run of the program."""
#        sen = self._test_program.sensors
#        self._fifo_data = {'Step1': ((sen.oDcVin1, 111.0), ),}  # 1 fail value
#        self._tester.test(('UUT1', ))
#        self.assertEqual(self._result.code, 'F')        # Must have failed
#        self.assertEqual(len(self._result.readings), 1) # Only 1 reading
#        self.assertEqual(self._steps, ['Step1'])        # 1 step only
