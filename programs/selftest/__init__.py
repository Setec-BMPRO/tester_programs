#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program."""

import logging

import tester
from . import support
from . import limit

LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Main(tester.testsequence.TestSequence):

    """Selfchecker Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # True if running on ATE2 tester
        self._is_ate2 = (physical_devices.tester_type == 'ATE2')
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('Checker', self._step_checker, None, True),
            ('DSO', self._step_dso, None, not self._is_ate2),
            ('ACSource', self._step_acsource, None, True),
            ('DCSource', self._step_dcsource, None, True),
            ('DCLoad', self._step_dcload, None, True),
            ('RelayDriver', self._step_relaydriver, None, True),
            ('Discharge', self._step_discharge, None, True),
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
        global d, s, m
        d = support.LogicalDevices(self._devices, self._is_ate2)
        s = support.Sensors(d, self._is_ate2)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_checker(self):
        """Test Checker Voltages."""
        if self._fifo:
            s.check12.store(11.8)
            for voltage in s.check5:
                voltage.store(5.1)

        d.acs.output(voltage=240, frequency=50, output=True)
        tester.MeasureGroup(m.dmm_check_v, timeout=2)

    def _step_dso(self):
        """Test DSO."""
        if self._fifo:
            for shield in s.shield:
                shield.store(6.0)
            for subch in s.subchan:
                subch.store(((8.0, 6.0, 4.0, 2.0),))
                for shield in s.shield:
                    shield.store(0.1)

        for shield in m.dmm_shield_off:
            shield.measure(timeout=1.0)
        for meas in m.dso_subchan:
            meas.measure(timeout=1.0)
            for shield in m.dmm_shield_on:
                shield.measure(timeout=1.0)

    def _step_dcsource(self):
        """Test DC Sources."""
        if self._fifo:
            for src in s.dcs:
                src.store((5.1, 10.2, 20.3, 35.4))

        for voltage, group in m.dmm_dcs:
            for src in d.dcs:
                src.output(voltage=voltage, output=True)
                src.opc()
            tester.MeasureGroup(group)

    def _step_acsource(self):
        """Test AC Source."""
        self.fifo_push(((s.Acs, (120, 240)), ))

        d.acs.configure(ocp='MAX', rng=300)
        for voltage, meas in m.dmm_Acs:
            d.acs.output(voltage=voltage, frequency=50, output=True)
            d.acs.opc()
            meas.measure(timeout=1.0)

    def _step_dcload(self):
        """Test DC Loads."""
        if self._fifo:
            for _ in range(1, 8):
                s.shunt.store((5e-3, 10e-3, 20e-3, 40e-3))

        for load in d.dcl:
            for current, meas in m.dmm_Shunt:
                load.output(current=current, output=True)
                load.opc()
                meas.measure(timeout=1.0)
            load.output(current=0.0, output=False)

    def _step_relaydriver(self):
        """Test Relay Drivers."""
        if self._fifo:
            s.Rla12V.store(11.9)
            for _ in range(23):
                s.Rla.store((0.7, 12.1))

        m.dmm_Rla12V.measure(timeout=1.0)
        for rly in d.rly:
            rly.set_on()
            rly.opc()
            m.dmm_RlaOn.measure(timeout=1.0)
            rly.set_off()
            rly.opc()
            m.dmm_RlaOff.measure(timeout=1.0)

    def _step_discharge(self):
        """Test Discharge."""
        if self._fifo:
            for disch in s.disch:
                disch.store((11.0, 0.0))

        d.disch.set_on()
        d.disch.opc()
        for disch in m.dmm_disch_on:
            disch.measure()
        d.disch.set_off()
        d.disch.opc()
        for disch in m.dmm_disch_off:
            disch.measure()
