#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program."""

import os
import inspect
import time

import tester
import sensor
import share
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._devices = devices
        self._fifo = fifo
        self.acsource = tester.ACSource(devices['ACS'])
        self.dmm = tester.DMM(devices['DMM'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_10vfixture = tester.DCSource(devices['DCS1'])
        self.dcs_5v = tester.DCSource(devices['DCS2'])
        self.dcl_24v = tester.DCLoad(devices['DCL1'])
        self.dcl_12v = tester.DCLoadParallel(
            ((tester.DCLoad(devices['DCL2']), 12),
             (tester.DCLoad(devices['DCL3']), 10)))
        self.dcl_5v = tester.DCLoad(devices['DCL4'])
        self.rla_pson = tester.Relay(devices['RLA1'])     # ON == Enable unit
        self.rla_12v2off = tester.Relay(devices['RLA2'])  # ON == 12V2 off
        self.rla_boot = tester.Relay(devices['RLA3'])     # ON == Asserted
        self.rla_reset = tester.Relay(devices['RLA4'])    # ON == Asserted
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = share.ProgramARM(limit.ARM_PORT, file)
        # Serial connection to the ARM console
        arm_ser = share.SimSerial(simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately - don't open until after programming
        arm_ser.port = limit.ARM_PORT
        self.arm = console.Console(arm_ser, verbose=False)

    def arm_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
            self.arm.puts(string_data, preflush, postflush, priority)

    def arm_calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self.arm['CAL_PFC'] = voltage
        self.arm['NVWRITE'] = True

    def arm_cal12v(self, voltage):
        """Issue 12V calibration commands."""
        self.arm['CAL_12V'] = voltage
        self.arm['NVWRITE'] = True

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.arm.close()
        # Switch off AC Source and discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.loads(i5=1.0, i12=5.0, i24=5.0)
        time.sleep(0.5)
        self.discharge.pulse()
        self.loads(i5=0, i12=0, i24=0)
        self.dcs_5v.output(0.0, False)
        for rla in (self.rla_12v2off, self.rla_pson,
                    self.rla_reset, self.rla_boot):
            rla.set_off()

    def loads(self, i5=None, i12=None, i24=None):
        """Set output loads."""
        if i5:
            self.dcl_5v.output(i5, output=True)
        if i12:
            self.dcl_12v.output(i12, output=True)
        if i24:
            self.dcl_24v.output(i24, output=True)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        d = logical_devices
        dmm = d.dmm
        self.o5v = sensor.Vdc(dmm, high=7, low=4, rng=10, res=0.001)
        self.o12v = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self.o12v2 = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self.o24v = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self.pwrfail = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.01)
        self.o3v3 = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.001)
        self.o12vpri = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self.pfc = sensor.Vdc(dmm, high=3, low=3, rng=1000, res=0.001)
        self.acin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.gpo = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self.lock = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self.part = sensor.Res(dmm, high=10, low=5, rng=1000, res=0.01)
        self.fanshort = sensor.Res(dmm, high=13, low=7, rng=1000, res=0.1)
        self.vdsfet = sensor.Vdc(dmm, high=14, low=8, rng=100, res=0.001)
        self.arm_acfreq = console.Sensor(d.arm, 'AcFreq')
        self.arm_acvolt = console.Sensor(d.arm, 'AcVolt')
        self.arm_5v = console.Sensor(d.arm, '5V')
        self.arm_12v = console.Sensor(d.arm, '12V')
        self.arm_24v = console.Sensor(d.arm, '24V')
        self.arm_swver = console.Sensor(
            d.arm, 'SwVer', rdgtype=sensor.ReadingString)
        self.arm_swbld = console.Sensor(
            d.arm, 'SwBld', rdgtype=sensor.ReadingString)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self._limits = limits
        self.dmm_lock = self._maker('FixtureLock', sense.lock)
        self.dmm_part = self._maker('PartCheck', sense.part)
        self.dmm_fanshort = self._maker('FanShort', sense.fanshort)
        self.dmm_acin = self._maker('InputFuse', sense.acin)
        self.dmm_12vpri = self._maker('12Vpri', sense.o12vpri)
        self.dmm_5vset = self._maker('5Vset', sense.o5v)
        self.dmm_5v = self._maker('5V', sense.o5v)
        self.dmm_12voff = self._maker('12Voff', sense.o12v)
        self.dmm_12vpre = self._maker('12Vpre', sense.o12v)
        self.dmm_12vset = self._maker('12Vset', sense.o12v)
        self.dmm_12v = self._maker('12V', sense.o12v)
        self.dmm_12v2off = self._maker('12V2off', sense.o12v2)
        self.dmm_12v2pre = self._maker('12V2pre', sense.o12v2)
        self.dmm_12v2 = self._maker('12V2', sense.o12v2)
        self.dmm_24voff = self._maker('24Voff', sense.o24v)
        self.dmm_24vpre = self._maker('24Vpre', sense.o24v)
        self.dmm_24v = self._maker('24V', sense.o24v)
        self.dmm_vdsfet = self._maker('VdsQ103', sense.vdsfet)
        self.dmm_3v3 = self._maker('3V3', sense.o3v3)
        self.dmm_pfcpre = self._maker('PFCpre', sense.pfc)
        self.dmm_pfcpost1 = self._maker('PFCpost1', sense.pfc, False)
        self.dmm_pfcpost2 = self._maker('PFCpost2', sense.pfc, False)
        self.dmm_pfcpost3 = self._maker('PFCpost3', sense.pfc, False)
        self.dmm_pfcpost4 = self._maker('PFCpost4', sense.pfc, False)
        self.dmm_pfcpost = self._maker('PFCpost', sense.pfc)
        self.dmm_pwrfail = self._maker('PwrFail', sense.pwrfail)
        self.arm_acfreq = self._maker('ARM-AcFreq', sense.arm_acfreq)
        self.arm_acvolt = self._maker('ARM-AcVolt', sense.arm_acvolt)
        self.arm_5v = self._maker('ARM-5V', sense.arm_5v)
        self.arm_12v = self._maker('ARM-12V', sense.arm_12v)
        self.arm_24v = self._maker('ARM-24V', sense.arm_24v)
        self.arm_swver = self._maker('SwVer', sense.arm_swver)
        self.arm_swbld = self._maker('SwBld', sense.arm_swbld)

    def _maker(self, limitname, sensor, position_fail=True):
        """Create a Measurement.

        @param limitname Test Limit name
        @param sensor Sensor to use
        @return tester.Measurement instance

        """
        if not position_fail:
            self._limits[limitname].position_fail = False
        return tester.Measurement(self._limits[limitname], sensor)
