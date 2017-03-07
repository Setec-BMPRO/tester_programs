#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import tester
from tester.testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_lo, lim_boolean
    )

LIMITS = tester.testlimit.limitset((
    lim_boolean('Notify', True),
    lim_hilo_percent('VoutNL', 13.85, 1.0),
    lim_hilo_percent('Vout', 13.85, 5.0),
    lim_lo('InOCP', 12.0),
    lim_hilo_delta('OCP', 14.0, 2.0),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """BC15 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('Load', self._step_loaded),
            )
        global d, s, m
        self._limits = LIMITS
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_poweron(self):
        """Power up the Unit and measure output with min load."""
        self.fifo_push(((s.ps_mode, True), (s.vout, 13.80), ))

        d.dcl.output(1.0, output=True)
        d.acsource.output(240.0, output=True)
        tester.MeasureGroup((m.ps_mode, m.vout_nl, ), timeout=5)

    def _step_loaded(self):
        """Load the Unit."""
        self.fifo_push(
            ((s.vout, (14.23, ) + (14.2, ) * 8 + (11.0, )),
             (s.ch_mode, True), ))

        d.dcl.output(10.0)
        tester.MeasureGroup((m.vout, m.ocp, m.ch_mode, ), timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.vout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.ps_mode = sensor.Notify(
            message=tester.translate('bc15_final', 'GoToPsMode'),
            caption=tester.translate('bc15_final', 'capPsMode'))
        self.ch_mode = sensor.Notify(
            message=tester.translate('bc15_final', 'GoToChargeMode'),
            caption=tester.translate('bc15_final', 'capChargeMode'))
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.vout,
            detect_limit=(limits['InOCP'], ),
            start=10.0, stop=17.0, step=0.5, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.vout_nl = Measurement(limits['VoutNL'], sense.vout)
        self.vout = Measurement(limits['Vout'], sense.vout)
        self.ps_mode = Measurement(limits['Notify'], sense.ps_mode)
        self.ch_mode = Measurement(limits['Notify'], sense.ch_mode)
        self.ocp = Measurement(limits['OCP'], sense.ocp)
