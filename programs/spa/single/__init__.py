#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spa SINGLE Initial Test Program.

Call 'self.abort()' to stop program running at end of current step.
'self._result_map' is a list of 'uut.Result' indexed by position.

"""

import time
import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

SGL_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None

# Scale factor for AC Input.
#   AC Source setting = AC Setting * factor
_AC_SCALE = 1.0
# Settling times after changing AC Input.
_AC_SETTLE_TIME = 0.2
# Maximum AC Source setting we will allow in ac_in().
_AC_VSET_MAX = 40.0

# From Spa Testing Notes Rev 1:
# i   Apply 12Vac, 50Hz.
# ii  LED must be operational.
# iii Average operating current must be 775mA ~ 825mA.
# iv  Whilst LED ON, adjust Vin to 10.5VAC +/- 0.1.
# v   Measure average LED operating current and input AC current.
# vi  Repeat iv & v above for 24VAC, 32VAC and 35VAC +/- 0.1.
# vii Average operating current for 24V to 35V AC must be between 720mA~880mA.
#     Average operating current at 10.5V must be between 650 mA ~ 880 mA.


class InitialSingle(tester.TestSequence):

    """Spa SINGLE Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerOn', self._step_poweron, None, True),
            ('Led12', self._step_led12, None, True),
            ('Led10', self._step_led10, None, True),
            ('Led24', self._step_led24, None, True),
            ('Led32', self._step_led32, None, True),
            ('Led35', self._step_led35, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # This is a multi-unit parallel program so we can't stop on errors.
        self.stop_on_failrdg = False
        # This is a multi-unit parallel program so we can't raise exceptions.
        tester.measure.exception_upon_fail(False)
        # Last AC Source set voltage
        self._last_vac = 0.0

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d)
        m = support.Measurements(s, self._limits)
        # Switch on DC Source that power the test fixture
        d.dcsAuxPos.output(voltage=15.0, output=True)
        d.dcsAuxNeg.output(voltage=15.0, output=True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        # Switch off DC Source that power the test fixture
        for dc in (d.dcsAuxPos, d.dcsAuxNeg):
            dc.output(voltage=0.0, output=False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_poweron(self):
        """Initial Power-Up."""
        self.fifo_push(((s.oAcVin, 12.01), ))
        self._ac_in(12.0, ramp=False, output=True)
        m.dmm_AcVin12.measure(timeout=1.0)

    def _step_led12(self):
        """LED current regulation 12Vac.

        Measure LED current and input AC current.

        """
        self.fifo_push(
            ((s.oAcVin, 12.01), (s.oAcIin1, 0.28 / 5), (s.oAcIin2, 0.28 / 5),
             (s.oAcIin3, 0.28 / 5), (s.oAcIin4, 0.28 / 5),
             (s.dso_led, ((7.51, 7.52, 7.53, 7.54), )), ))
        MeasureGroup((m.dmm_AcVin12, m.dso_led, m.dmm_AcIin1_12,
                      m.dmm_AcIin2_12, m.dmm_AcIin3_12, m.dmm_AcIin4_12))

    def _step_led10(self):
        """LED current regulation 10.5Vac.

        Measure LED current and input AC current.

        """
        self.fifo_push(
            ((s.oAcVin, 10.51), (s.oAcIin1, 0.24 / 5), (s.oAcIin2, 0.24 / 5),
             (s.oAcIin3, 0.24 / 5), (s.oAcIin4, 0.24 / 5),
             (s.dso_led, ((7.1, 7.2, 7.3, 7.4), )), ))
        self._ac_in(10.5)
        MeasureGroup((m.dmm_AcVin10, m.dso_led10, m.dmm_AcIin1_10,
                      m.dmm_AcIin2_10, m.dmm_AcIin3_10, m.dmm_AcIin4_10))

    def _step_led24(self):
        """LED current regulation 24Vac.

        Measure LED current and input AC current.

        """
        self.fifo_push(
            ((s.oAcVin, 24.01), (s.oAcIin1, 0.2 / 5), (s.oAcIin2, 0.2 / 5),
             (s.oAcIin3, 0.2 / 5), (s.oAcIin4, 0.2 / 5),
             (s.dso_led, ((7.61, 7.62, 7.63, 7.64), )), ))
        self._ac_in(24.0)
        MeasureGroup((m.dmm_AcVin24, m.dso_led, m.dmm_AcIin1_24,
                      m.dmm_AcIin2_24, m.dmm_AcIin3_24, m.dmm_AcIin4_24))

    def _step_led32(self):
        """LED current regulation 32Vac.

        Measure LED current and input AC current.

        """
        self.fifo_push(
            ((s.oAcVin, 32.01), (s.oAcIin1, 0.16 / 5), (s.oAcIin2, 0.16 / 5),
             (s.oAcIin3, 0.16 / 5), (s.oAcIin4, 0.16 / 5),
             (s.dso_led, ((7.71, 7.72, 7.73, 7.74), )), ))
        self._ac_in(32.0)
        MeasureGroup((m.dmm_AcVin32, m.dso_led, m.dmm_AcIin1_32,
                      m.dmm_AcIin2_32, m.dmm_AcIin3_32, m.dmm_AcIin4_32))

    def _step_led35(self):
        """LED current regulation 35Vac.

        Measure LED current and input AC current.

        """
        self.fifo_push(
            ((s.oAcVin, 35.01), (s.oAcIin1, 0.1 / 5), (s.oAcIin2, 0.1 / 5),
             (s.oAcIin3, 0.1 / 5), (s.oAcIin4, 0.1 / 5),
             (s.dso_led, ((7.81, 7.82, 7.83, 7.84), )), ))
        self._ac_in(35.0)
        MeasureGroup((m.dmm_AcVin35, m.dso_led, m.dmm_AcIin1_35,
                      m.dmm_AcIin2_35, m.dmm_AcIin3_35, m.dmm_AcIin4_35))

    def _ac_in(self, vset, output=True, ramp=True, correct=True):
        """Set the AC Source for the target input voltage."""
        vsrc = vset * _AC_SCALE
        vsrc += {0.0: 0.0, 10.5: 0.0, 12.0: 0.0,
                 24.0: 0.0, 32.0: 0.0, 35.0: 0.0,
                 }[vset]
        # A just-in-case check to stop blowing up units...
        if vsrc > _AC_VSET_MAX:
            raise ValueError('AC Source setting too high')
        # Switch off immediately, otherwise ramp to change voltage
        if vset < 10.0:
            ramp = False
        if ramp:
            delay = 0.01
            step = 2.0
            d.acsource.linear(
                start=self._last_vac, end=vsrc, step=step, delay=delay)
        else:
            d.acsource.output(voltage=vsrc, output=output)
        self._last_vac = vsrc
        # Correct the AC voltage to allow for drops
        if correct and vset > 10.0:
            s.oAcVin.configure()
            s.oAcVin.opc()
            self.fifo_push(((s.oAcVin, vset), ))
            for _ in range(4):
                vact = s.oAcVin.read()[0]
                verror = vset - vact
                if abs(verror) < 0.09:
                    break
                if abs(verror) < 3.0:
                    vsrc += verror * _AC_SCALE
                d.acsource.output(voltage=vsrc, output=output)
            time.sleep(_AC_SETTLE_TIME)
