#!/usr/bin/env python3
"""2040 Initial Test Program."""

import logging
import time

import tester
from . import support
from . import limit

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """2040 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('SecCheck', self._step_sec_check, None, True),
            ('DCPowerOn', self._step_dcpower_on, None, True),
            ('ACPowerOn', self._step_acpower_on, None, True),
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
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_Vout.output(1.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), ))

        m.dmm_Lock.measure(timeout=5)

    def _step_sec_check(self):
        """Apply External DC voltage to output and measure voltages."""
        self.fifo_push(((s.oVout, 20.0), (s.oSD, 20.0), (s.oGreen, 17.0), ))
        t.sec_chk.run()

    def _step_dcpower_on(self):
        """Test with DC power in.

        Power with DC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oDCin, (10.0, 40.0, 25.0)), (s.oGreen, 17.0),
             (s.oRedDC, (12.0, 2.5)), (s.oVccDC, (12.0,) * 3),
             (s.oVout, (20.0, ) * 15 + (18.0, ), ), (s.oSD, 4.0),))
        t.dcpwr_on.run()

    def _step_acpower_on(self):
        """Test with AC power in.

        Power with AC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oACin, (90.0, 265.0, 240.0)), (s.oGreen, 17.0),
             (s.oRedAC, 12.0), (s.oVbus, (130.0, 340)),
             (s.oVccAC, (13.0,) * 3), (s.oVout, (20.0, ) * 15 + (18.0, ), ), ))
        t.acpwr_on.run()
