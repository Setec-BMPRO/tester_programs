#!/usr/bin/env python3
"""Drifter Initial Test Program."""

from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *

from . import pic_driver

sensor = tester.sensor


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
        dmm = logical_devices.dmm
        self.oMirPIC = sensor.Mirror()
        self.oMirErrorV = sensor.Mirror()
        self.oMirErrorI = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVsw = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVref = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.001)
        self.oVcc = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.oIsense = sensor.Vdc(
            dmm, high=5, low=1, rng=10, res=0.00001, scale=-1000.0)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self.o0V8 = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        self.oPic_Status = pic_driver.Sensor(picdev, 'PIC-NvStatus')
        self.oPic_ZeroChk = pic_driver.Sensor(picdev, 'PIC-ZeroCheck')
        self.oPic_Vin = pic_driver.Sensor(picdev, 'PIC-Vin')
        self.opic_isense = pic_driver.Sensor(picdev, 'PIC-Isense')
        self.oPic_Vfactor = pic_driver.Sensor(picdev, 'PIC-Vfactor')
        self.oPic_Ifactor = pic_driver.Sensor(picdev, 'PIC-Ifactor')
        self.oPic_Ioffset = pic_driver.Sensor(picdev, 'PIC-Ioffset')
        self.oPic_Ithreshold = pic_driver.Sensor(picdev, 'PIC-Ithreshold')

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
        self.pic_Status = Measurement(limits['Status 0'], sense.oPic_Status)
        self.pic_ZeroChk = Measurement(limits['ZeroChk'], sense.oPic_ZeroChk)
        self.pic_vin = Measurement(limits['PicVin'], sense.oPic_Vin)
        self.pic_isense = Measurement(limits['PicIsense'], sense.opic_isense)
        self.pic_Vfactor = Measurement(limits['Vfactor'], sense.oPic_Vfactor)
        self.pic_Ifactor = Measurement(limits['Ifactor'], sense.oPic_Ifactor)
        self.pic_Ioffset = Measurement(limits['Ioffset'], sense.oPic_Ioffset)
        self.pic_Ithreshold = Measurement(
            limits['Ithreshold'], sense.oPic_Ithreshold)


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
        dcs1 = DcSubStep(
            setting=((d.dcs_Vin, 12.0), ), output=True, delay=2)
        msr1 = MeasureSubStep((m.dmm_vin, m.dmm_Vcc), timeout=5)
        self.pwr_up = Step((dcs1, msr1))
        # Reset:
        dcs1 = DcSubStep(setting=((d.dcs_Vin, 0.0),))
        dcs2 = DcSubStep(setting=((d.dcs_Vin, 12.0), ), delay=4)
        msr1 = MeasureSubStep((m.dmm_vin, m.dmm_Vcc), timeout=5)
        self.reset = Step((dcs1, dcs2, msr1))
