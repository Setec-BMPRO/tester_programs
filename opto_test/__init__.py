#!/usr/bin/env python3
"""Opto Test Program."""

import logging

import tester
from . import support
from . import limit

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


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
            ('InputAdj', self._step_in_adj, None, True),
            ('OutputAdj', self._step_out_adj, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._Iin = None
        self._Iout = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_in_adj(self):
        """Input adjust and measure.

            Adjust input source voltage to get Iin = 1mA.
            Measure Iin.

         """
        self.fifo_push(((s.oIsen, (0.5, ) * 15 + (1.0, 1.02), ), ))
        d.dcs_vin.output(22.0, True)
        m.ramp_VinAdj.measure(timeout=5)
        self._Iin = m.dmm_Iin.measure(timeout=5)[1][0]

    def _step_out_adj(self):
        """Output adjust and measure.

            Adjust output source voltage to get 5V across collector-emitter.
            Measure Iout.
            Calculate CTR.

         """
        for i in range(20):
            self.fifo_push(((s.Vce[i], (-4.5, ) * 15 + (-5.0, ), ),
                          (s.Iout[i], 0.75), ))
            d.dcs_vout.output(5.0, True)
            tester.testsequence.path_push('Opto{}'.format(i + 1))
            m.ramp_VoutAdj[i].measure(timeout=5)
            self._Iout = m.dmm_Iout[i].measure(timeout=5)[1][0]
            self._step_cal_ctr()
            tester.testsequence.path_pop()

    def _step_cal_ctr(self):
        """Calculate current transfer ratio and measure."""
        ctr = (self._Iout / self._Iin) * 100
        s.oMirCtr.store(ctr)
        m.dmm_ctr.measure()
