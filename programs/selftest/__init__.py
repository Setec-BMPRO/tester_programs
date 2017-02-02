#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program."""

import logging
import tester
from . import support
from . import limit

LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Main(tester.testsequence.TestSequence):

    """Selfchecker Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # True if running on ATE2 tester
        self._is_ate2 = (physical_devices.tester_type == 'ATE2')
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('ACSource', self._step_acsource),
            tester.TestStep('Checker', self._step_checker),
            tester.TestStep('DSO', self._step_dso, not self._is_ate2),
            tester.TestStep('DCSource', self._step_dcsource),
            tester.TestStep('DCLoad', self._step_dcload),
            tester.TestStep('RelayDriver', self._step_relaydriver),
            tester.TestStep('Discharge', self._step_discharge),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self, parameter):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices, self._is_ate2)
        s = support.Sensors(d, self._is_ate2)
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

    def _step_acsource(self):
        """Apply AC inputs to Fixture and measure ac voltages."""
        self.fifo_push(((s.oAcs, (120, 240)), ))
        d.acsource.configure(ocp='MAX', rng=300)
        t.acs.run()

    def _step_checker(self):
        """With 240Vac input applied, measure Fixture dc voltages."""
        self.fifo_push(
            ((s.o12V, 12.0), (s.o5Va, 5.0), (s.o5Vb, 5.0), (s.o5Vc, 5.0),
             (s.o5Vd, 5.0), (s.o5Ve, 5.0), ))
        t.check.run()

    def _step_dso(self):
        """Test DSO.

        Measure all DSO input connector shields off.
        The 4 channels are connected to 8V, 6V, 4V, 2V from the Fixture.
        For each subchannel in turn, measure voltages on all 4 inputs and
        measure all shields on.

        """
        self.fifo_push(((s.oShield1, 6.0), (s.oShield2, 6.0),
                (s.oShield3, 6.0), (s.oShield4, 6.0), ))
        if self.fifo:
            for subch in s.subchan:
                subch.store(((8.0, 6.0, 4.0, 2.0),))
                self.fifo_push(((s.oShield1, 0.0), (s.oShield2, 0.0),
                        (s.oShield3, 0.0), (s.oShield4, 0.0), ))
        t.shld_off.run()
        for meas in m.dso_subchan:
            meas.measure(timeout=5.0)
            t.shld_on.run()

    def _step_dcsource(self):
        """Test DC Sources.

        Set all DC Sources together in the steps 5V, 10V, 20V, 35V
        After each step measure voltages on all DC Sources.

        """
        if self.fifo:
            for src in s.dcs:
                src.store((5.0, 10.0, 20.0, 35.0))
        for step, group in m.dmm_dcs:
            for src in d.dcs:
                src.output(voltage=step, output=True)
                src.opc()
            tester.MeasureGroup(group)

    def _step_dcload(self):
        """Test DC Loads.

        All DC Loads are connected via a 1mR shunt to the Fixture 5V/50A PSU.
        Set each DC Load in turn to 5A, 10A, 20A, 40A and measure the
        actual current through the shunt for the DC Load.

        """
        self.fifo_push(
            ((s.oShunt, (5e-3, 10e-3, 20e-3, 40e-3) * 7), ))
        for load in d.dcl:
            for current, meas in m.dmm_Shunt:
                load.output(current=current, output=True)
                load.opc()
                meas.measure(timeout=5.0)
            load.output(current=0.0, output=False)

    def _step_relaydriver(self):
        """Test Relay Drivers.

        Measure Relay Driver 12V supply.
        Switch on/off each Relay Driver in turn and measure.

        """
        self.fifo_push(
            ((s.oRla12V, 12.0), (s.oRla, (0.5, 12.0) * 22), ))
        m.dmm_Rla12V.measure(timeout=1.0)
        for rly in d.relays:
            rly.set_on()
            rly.opc()
            m.dmm_RlaOn.measure(timeout=5.0)
            rly.set_off()
            rly.opc()
            m.dmm_RlaOff.measure(timeout=5.0)

    def _step_discharge(self):
        """Test Discharge.

        Switch Discharger on/off and measure.

        """
        self.fifo_push(((s.oDisch1, (10.0, 0.0)), (s.oDisch2, (10.0, 0.0)),
                        (s.oDisch3, (10.0, 0.0)), ))
        d.discharger.set_on()
        d.discharger.opc()
        t.disch_on.run()
        d.discharger.set_off()
        d.discharger.opc()
        t.disch_off.run()
