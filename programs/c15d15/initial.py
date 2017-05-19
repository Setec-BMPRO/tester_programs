#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Initial Test Program."""
# FIXME: Upgrade this program to 3rd Generation standards with unittest.

import tester
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_lo)

VIN_SET = 30.0      # Input voltage setting
VOUT = 15.5
IOUT_FL = 1.0       # Max output current
OCP_START = 0.9     # OCP measurement parameters
OCP_STOP = 1.3
OCP_STEP = 0.01
OCP_DELAY = 0.5

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('Vin', VIN_SET, 2.0),
    lim_hilo('Vcc', 11.0, 14.0),
    lim_hilo_percent('VoutNL', VOUT, 2.0),
    lim_hilo('VoutFL', VOUT * (1.0 - 0.035), VOUT * (1.0 + 0.02)),
    lim_hilo('VoutOCP', 12.5, VOUT * (1.0 - 0.035)),
    lim_lo('LedOff', 0.5),
    lim_hilo('LedOn', 7.0, 13.5),
    lim_lo('inOCP', 13.6),
    lim_hilo('OCP', 1.03, 1.17),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """C15D-15 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Charging', self._step_charging),
            )
        self._limits = LIMITS
        global d, s, m
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

    def _step_power_up(self):
        """Power up."""
        self.fifo_push(
            ((s.vin, 30.0), (s.vcc, 13.0), (s.vout, 15.5),
             (s.led_green, 10.0), (s.led_yellow, 0.2), ))

        d.dcl.output(0.0, output=True)
        d.dcs_input.output(VIN_SET, output=True)
        tester.MeasureGroup(
            (m.dmm_vin, m.dmm_vcc, m.dmm_vout_nl, m.dmm_green_on,
             m.dmm_yellow_off, ), timeout=5)

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.vout, (15.5, ) * 22 + (13.5, ), ), ))

        m.ramp_ocp.measure()
        d.dcl.output(0.0)

    def _step_charging(self):
        """Load into OCP for charging check."""
        self.fifo_push(
            ((s.vout, (13.5, 15.5, )),
             (s.led_green, 10.0), (s.led_yellow, 10.0), ))

        d.rla_load.set_on()
        tester.MeasureGroup(
            (m.dmm_vout_ocp, m.dmm_green_on, m.dmm_yellow_on, ),
            timeout=5)
        d.rla_load.set_off()
        tester.MeasureGroup((m.dmm_vout_nl, ), timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS1'])
        self.dcl = tester.DCLoad(devices['DCL1'])
        self.rla_load = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.dcs_input.output(0.0, False)
        self.dcl.output(0.0, False)
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.vin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.vcc = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self.led_green = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.led_yellow = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self.vout = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.vout,
            detect_limit=(limits['inOCP'], ),
            start=OCP_START, stop=OCP_STOP, step=OCP_STEP, delay=OCP_DELAY)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_vin = Measurement(limits['Vin'], sense.vin)
        self.dmm_vcc = Measurement(limits['Vcc'], sense.vcc)
        self.dmm_vout_nl = Measurement(limits['VoutNL'], sense.vout)
        self.dmm_vout_fl = Measurement(limits['VoutFL'], sense.vout)
        self.dmm_vout_ocp = Measurement(limits['VoutOCP'], sense.vout)
        self.dmm_green_on = Measurement(limits['LedOn'], sense.led_green)
        self.dmm_yellow_off = Measurement(limits['LedOff'], sense.led_yellow)
        self.dmm_yellow_on = Measurement(limits['LedOn'], sense.led_yellow)
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
