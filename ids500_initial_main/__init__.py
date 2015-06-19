#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Main Test Program."""

import logging
import time

import tester.testsequence
import tester.measure
import tester.sensor

from . import support
from . import limit


LIMIT_DATA = limit.DATA


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.testsequence.TestSequence):

    """IDS-500 Initial Main Test Program."""

    def __init__(self, selection, physical_devices, test_limits):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
                    ('FixtureLock', self._step_fixture_lock, None, True),
                    ('PowerUp', self._step_power_up, None, True),
                    ('ErrorCheck', self._step_error_check, None, True),
                    )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence)
        self._logger = logging.getLogger('.'.join(
                                        (__name__,
                                         self.__class__.__name__)))
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

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            d.acsource.output(voltage=0.0, output=False)
            d.dcl_Tec.output(0.1)
            d.dcl_15Vp.output(1.0)
            d.dcl_15Vpsw.output(0.0)
            d.dcl_5V.output(5.0)
            if self._fifo:
                d.discharge.pulse(0.1)
            else:
                time.sleep(1)
                d.discharge.pulse()
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self._fifo_push(((s.Lock, 10.0), ))

        m.dmm_Lock.measure(timeout=5)

    def _step_power_up(self):
        """Set min load, apply input AC and measure voltages."""
        self._fifo_push(((s.oVbus, 340.0), (s.oTec, 0.0), (s.oTecVmon, 0.0),
                         (s.oLdd, 0.0), (s.oIsVmon, 0.0), (s.o15V, 0.0),
                         (s.om15V, 0.0), (s.o15Vp, 0.0), (s.o15VpSw, 0.0),
                         (s.o5V, 0.0), ))

        t.pwr_up.run()

