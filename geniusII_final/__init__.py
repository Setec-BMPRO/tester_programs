#!/usr/bin/env python3
"""Final Test Program for GENIUS-II and GENIUS-II-H."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA         # GENIUS-II limits
LIMIT_DATA_H = limit.DATA_H     # GENIUS-II-H limits


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """GENIUS-II Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('InputRes', self._step_inres, None, True),
            ('PowerOn', self._step_poweron, None, True),
            ('BattFuse', self._step_battfuse, None, True),
            ('OCP', self._step_ocp, None, True),
            ('RemoteSw', self._step_remote_sw, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
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
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

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
