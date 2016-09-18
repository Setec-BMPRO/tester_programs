#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Initial Test Program."""

import os
import inspect
from pydispatch import dispatcher
import share
import tester
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, limits, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_RS232 = tester.DCSource(devices['DCS1'])
        self.dcs_SlopeCal = tester.DCSource(devices['DCS2'])
        self.dcs_Vin = tester.DCSource(devices['DCS3'])
        self.rla_Prog = tester.Relay(devices['RLA1'])
        self.rla_ZeroCal = tester.Relay(devices['RLA2'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            limits['Software'].limit, folder, '18F87J93', self.rla_Prog)
        # Serial connection to the console
        pic_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=5)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = limit.PIC_PORT
        self.pic = console.Console(pic_ser)

    def pic_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.pic.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.pic.close()
        for dcs in (self.dcs_RS232, self.dcs_SlopeCal, self.dcs_Vin):
            dcs.output(0.0, output=False)
        for rla in (self.rla_Prog, self.rla_ZeroCal):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        pic = logical_devices.pic
        sensor = tester.sensor
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
        self.pic_Status = console.Sensor(pic, 'NVSTATUS')
        self.pic_ZeroChk = console.Sensor(pic, 'ZERO_CURRENT')
        self.pic_Vin = console.Sensor(pic, 'VOLTAGE')
        self.pic_isense = console.Sensor(pic, 'CURRENT')
        self.pic_Vfactor = console.Sensor(pic, 'V_FACTOR')
        self.pic_Ifactor = console.Sensor(pic, 'I_FACTOR')
        self.pic_Ioffset = console.Sensor(pic, 'CAL_OFFSET_CURRENT')
        self.pic_Ithreshold = console.Sensor(
            pic, 'ZERO-CURRENT-DISPLAY-THRESHOLD')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirErrorV.flush()
        self.oMirErrorI.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
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
        self.pic_isense = Measurement(limits['PicIsense'], sense.pic_isense)
        self.pic_Vfactor = Measurement(limits['PicVfactor'], sense.pic_Vfactor)
        self.pic_Ifactor = Measurement(limits['PicIfactor'], sense.pic_Ifactor)
        self.pic_Ioffset = Measurement(limits['PicIoffset'], sense.pic_Ioffset)
        self.pic_Ithreshold = Measurement(
            limits['PicIthreshold'], sense.pic_Ithreshold)
