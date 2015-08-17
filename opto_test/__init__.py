#!/usr/bin/env python3
"""Opto Test Program."""

import logging

import tester
from . import support
from . import limit


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Opto Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('VinAdj', self._step_vin_adj, None, True),
            ('VoutAdj', self._step_vout_adj, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_vin_adj(self):
        """Adjust input voltage for common Iin = 1mA."""
        self.fifo_push(((s.oIin, (0.5, ) * 15 + (1.0, ), ),
                      (s.oIin, 1.02), ))
        d.dcs_vin.output(22.0, True)
        m.ramp_VinAdj.measure(timeout=5)
        self.Isen = m.dmm_Isen.measure(timeout=5)[1][0]

    def _step_vout_adj(self):
        """Adjust output voltage to get 5V across the collector/emitter."""
        self.fifo_push(((s.oVce1, (-4.5, ) * 15 + (-5.0, ), ),
                      (s.oIout1, 0.75), ))
        d.dcs_vout.output(4.95, True)
        m.ramp_VoutAdj.measure(timeout=5)
        self.Iout1 = m.dmm_Iout1.measure(timeout=5)[1][0]
        self._step_cal_ctr()

    def _step_cal_ctr(self):
        """Calculate current transfer ratio."""
        ctr = (self.Iout1 / self.Isen) * 100
        s.oMirCtr.store(ctr)
        m.dmm_ctr.measure()
