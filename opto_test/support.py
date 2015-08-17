#!/usr/bin/env python3
"""Opto Test Program.

        Logical Devices
        Sensors
        Measurements

"""
from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_vin = dcsource.DCSource(devices['DCS1'])
        self.dcs_vout = dcsource.DCSource(devices['DCS2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_vin, self.dcs_vout):
            dcs.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits
           @param trek2 Trek2 ARM console driver

        """
        dmm = logical_devices.dmm
        self.oMirCtr = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)

        self.oIin = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.oVinAdj = sensor.Ramp(
            stimulus=logical_devices.dcs_vin, sensor=self.oIin,
            detect_limit=(limits['Iin'], ),
            start=22.0, stop=24.0, step=0.05, delay=0.1)
        self.oVce1 = sensor.Vdc(dmm, high=5, low=2, rng=10, res=0.001)
        self.oVoutAdj = sensor.Ramp(
            stimulus=logical_devices.dcs_vout, sensor=self.oVce1,
            detect_limit=(limits['Vce'], ),
            start=4.95, stop=7.0, step=0.05, delay=0.1)
        self.oIout1 = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirCtr.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_ctr = Measurement(limits['CTR'], sense.oMirCtr)

        self.ramp_VinAdj = Measurement(limits['VinAdj'], sense.oVinAdj)
        self.dmm_Isen = Measurement(limits['Isen'], sense.oIin)
        self.ramp_VoutAdj = Measurement(limits['VoutAdj'], sense.oVoutAdj)
        self.dmm_Iout1 = Measurement(limits['Iout'], sense.oIout1)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
#        d = logical_devices
#        m = measurements
