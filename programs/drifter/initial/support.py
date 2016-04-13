#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Initial Test Program."""

from pydispatch import dispatcher
import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from ..console import Console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_RS232 = dcsource.DCSource(devices['DCS1'])
        self.dcs_SlopeCal = dcsource.DCSource(devices['DCS2'])
        self.dcs_Vin = dcsource.DCSource(devices['DCS3'])
        self.rla_Prog = relay.Relay(devices['RLA1'])
        self.rla_ZeroCal = relay.Relay(devices['RLA2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_RS232, self.dcs_SlopeCal, self.dcs_Vin):
            dcs.output(0.0, output=False)
        # Switch off all Relays
        for rla in (self.rla_Prog, self.rla_ZeroCal):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, picdev):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        self.oMirPIC = sensor.Mirror()
        self.oMirErrorV = sensor.Mirror()
        self.oMirErrorI = sensor.Mirror()
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVsw = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVref = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.001)
        self.oVcc = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.oIsense = sensor.Vdc(
            dmm, high=5, low=1, rng=10, res=0.00001, scale=-1000.0)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self.o0V8 = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        self.pic_Status = Console.Sensor(picdev, 'NVSTATUS')
        self.pic_ZeroChk = Console.Sensor(picdev, 'ZERO_CURRENT')
        self.pic_Vin = Console.Sensor(picdev, 'VOLTAGE')
        self.pic_isense = Console.Sensor(picdev, 'CURRENT')
        self.pic_Vfactor = Console.Sensor(picdev, 'V_FACTOR')
        self.pic_Ifactor = Console.Sensor(picdev, 'I_FACTOR')
        self.pic_Ioffset = Console.Sensor(picdev, 'CAL_OFFSET_CURRENT')
        self.pic_Ithreshold = Console.Sensor(
            picdev, 'ZERO-CURRENT-DISPLAY-THRESHOLD')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()
        self.oMirErrorV.flush()
        self.oMirErrorI.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmPIC = Measurement(limits['Program'], sense.oMirPIC)
        self.ErrorV = Measurement(limits['%ErrorV'], sense.oMirErrorV)
        self.CalV = Measurement(limits['%CalV'], sense.oMirErrorV)
        self.ErrorI = Measurement(limits['%ErrorI'], sense.oMirErrorI)
        self.CalI = Measurement(limits['%CalI'], sense.oMirErrorI)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_Vsw = Measurement(limits['Vsw'], sense.oVsw)
        self.dmm_Vref = Measurement(limits['Vref'], sense.oVref)
        self.dmm_Vcc = Measurement(limits['Vcc'], sense.oVcc)
        self.dmm_isense = Measurement(limits['Isense'], sense.oIsense)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_0V8 = Measurement(limits['0V8'], sense.o0V8)
        self.pic_Status = Measurement(limits['PicStatus 0'], sense.pic_Status)
        self.pic_ZeroChk = Measurement(limits['PicZeroChk'], sense.pic_ZeroChk)
        self.pic_vin = Measurement(limits['PicVin'], sense.pic_Vin)
        self.pic_isense = Measurement(limits['PicIsense'], sense.opic_isense)
        self.pic_Vfactor = Measurement(limits['PicVfactor'], sense.pic_Vfactor)
        self.pic_Ifactor = Measurement(limits['PicIfactor'], sense.pic_Ifactor)
        self.pic_Ioffset = Measurement(limits['PicIoffset'], sense.pic_Ioffset)
        self.pic_Ithreshold = Measurement(
            limits['PicIthreshold'], sense.pic_Ithreshold)
