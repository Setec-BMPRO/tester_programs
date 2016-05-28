#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETrac-II Initial Test Program."""

from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_Vin = dcsource.DCSource(devices['DCS1'])
        self.rla_SS = relay.Relay(devices['RLA1'])
        self.rla_Prog = relay.Relay(devices['RLA2'])
        self.rla_BattLoad = relay.Relay(devices['RLA3'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.dcs_Vin.output(0.0, False)
        for rla in (self.rla_SS, self.rla_Prog, self.rla_BattLoad):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirPIC = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVin2 = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.o5Vusb = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmPIC = Measurement(limits['Program'], sense.oMirPIC)
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_Vin2 = Measurement(limits['Vin2'], sense.oVin2)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_5Vusb = Measurement(limits['5Vusb'], sense.o5Vusb)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:
        rly1 = RelaySubStep(((d.rla_SS, True), ))
        dcs1 = DcSubStep(setting=((d.dcs_Vin, 13.0),), output=True)
        msr1 = MeasureSubStep(
            (m.dmm_Vin, m.dmm_Vin2, m.dmm_5V, ), timeout=10)
        self.pwr_up = Step((rly1, dcs1, msr1))
        # Load:
        msr1 = MeasureSubStep(
            (m.dmm_5Vusb, m.dmm_Vbat, ), timeout=10)
        rly1 = RelaySubStep(((d.rla_BattLoad, True), ))
        msr2 = MeasureSubStep((m.dmm_Vbat, ), timeout=10)
        self.load = Step((msr1, rly1, msr2))
