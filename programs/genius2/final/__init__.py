#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Test Program for GENIUS-II and GENIUS-II-H."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

FIN_LIMIT = limit.DATA         # GENIUS-II limits
FIN_LIMIT_H = limit.DATA_H     # GENIUS-II-H limits


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """GENIUS-II Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('InputRes', self._step_inres),
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('BattFuse', self._step_battfuse),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is a GENIUS-II-H if BattLoad current > 20A
        self._fullload = test_limits['MaxBattLoad'].limit
        self._isH = (self._fullload > 20)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global m, d, s, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_inres(self):
        """Verify that the hand loaded input discharge resistors are there."""
        self.fifo_push(((s.oInpRes, 135000), ))

        m.dmm_InpRes.measure(timeout=5)

    def _step_poweron(self):
        """Switch on unit at 240Vac, no load."""
        self.fifo_push(((s.oVout, 13.6), (s.oVbat, 13.6)))

        t.pwr_on.run()

    def _step_battfuse(self):
        """Remove and insert battery fuse, check red LED."""
        self.fifo_push(((s.oYesNoFuseOut, True), (s.oVbat, 0.0),
                        (s.oYesNoFuseIn, True), (s.oVout, 13.6)))
        MeasureGroup(
            (m.ui_YesNoFuseOut, m.dmm_VbatOff, m.ui_YesNoFuseIn, m.dmm_Vout),
            timeout=5)

    def _step_ocp(self):
        """
        Ramp up load until OCP.

        Shutdown and recover.

        """
        self.fifo_push(((s.oVout, (13.5, ) * 11 + (13.0, ), ),
                        (s.oVout, (0.1, 13.6, 13.6)), (s.oVbat, 13.6)))
        d.dcl.output(0.0, output=True)
        d.dcl.binary(0.0, 32.0, 5.0)
        if self._isH:
            m.ramp_OCP_H.measure()
            t.shdnH.run()
        else:
            m.ramp_OCP.measure()
            t.shdn.run()

    def _step_remote_sw(self):
        """
        Switch off AC, apply external Vbat.

        Check function of remote switch.

        """
        self.fifo_push(((s.oVbat, 12.0), (s.oVout, (12.0, 0.0, 12.0)), ))
        t.remote_sw.run()
