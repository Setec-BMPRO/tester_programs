#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Initial Test Program."""

import sensor
import tester
from . import limit

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS1'])
        self.dcl = tester.DCLoad(devices['DCL1'])
        self.rla_load = tester.Relay(devices['RLA1'])
# FIXME: Remove RLA1,3 from fixture. Move RLA2 to RLA1

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
        self.vin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.vcc = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self.led_green = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.led_yellow = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self.vout = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.vout,
            detect_limit=(limits['inOCP'], ),
            start=limit.OCP_START, stop=limit.OCP_STOP,
            step=limit.OCP_STEP, delay=limit.OCP_DELAY)


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
