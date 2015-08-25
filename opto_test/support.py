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
translate = tester.translate


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

        self.oIsen = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.oVinAdj1 = sensor.Ramp(
            stimulus=logical_devices.dcs_vin, sensor=self.oIsen,
            detect_limit=(limits['Isen1'], ),
            start=22.0, stop=24.0, step=0.01, delay=0.02, reset=False)
        self.oVinAdj10 = sensor.Ramp(
            stimulus=logical_devices.dcs_vin, sensor=self.oIsen,
            detect_limit=(limits['Isen10'], ),
            start=31.0, stop=33.0, step=0.01, delay=0.02, reset=False)
        # Generate a list of 20 collector-emitter voltage sensors.
        self.Vce = []
        for i in range(20):
            s = sensor.Vdc(dmm, high=(i + 5), low=2, rng=10, res=0.001)
            self.Vce.append(s)
        # Generate a list of 20 VoutAdj ramp sensors.
        self.VoutAdj = []
        for i in range(20):
            s = sensor.Ramp(
                stimulus=logical_devices.dcs_vout, sensor=self.Vce[i],
                detect_limit=(limits['Vsen'], ),
                start=5.0, stop=8.0, step=0.05, delay=0.02, reset=False)
            self.VoutAdj.append(s)
        # Generate a list of 20 Iout voltage sensors.
        self.Iout = []
        for i in range(20):
            s = sensor.Vdc(dmm, high=(i + 5), low=1, rng=10, res=0.001)
            self.Iout.append(s)

        tester.TranslationContext = 'opto_test'
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))

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
        self.dmm_Iin1 = Measurement(limits['Iin1'], sense.oIsen)
        self.dmm_Iin10 = Measurement(limits['Iin10'], sense.oIsen)
        self.ramp_VinAdj1 = Measurement(limits['VinAdj'], sense.oVinAdj1)
        self.ramp_VinAdj10 = Measurement(limits['VinAdj'], sense.oVinAdj10)
        # Generate a tuple of 20 collector-emitter voltage measurements.
        self.dmm_Vce = []
        for sen in sense.Vce:
            m = Measurement(limits['Vce'], sen)
            self.dmm_Vce.append(m)
        # Generate a tuple of 20 VoutAdj ramp measurements.
        self.ramp_VoutAdj = []
        for sen in sense.VoutAdj:
            m = Measurement(limits['VoutAdj'], sen)
            self.ramp_VoutAdj.append(m)
        # Generate a tuple of 20 Iout voltage measurements.
        self.dmm_Iout = []
        for sen in sense.Iout:
            m = Measurement(limits['Iout'], sen)
            self.dmm_Iout.append(m)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
