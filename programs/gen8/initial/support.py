#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program."""

from pydispatch import dispatcher
import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from share import Sensor as con_sensor
from share import SimSerial
from . import limit
from ..console import Console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._devices = devices
        self._fifo = fifo
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dmm = dmm.DMM(devices['DMM'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_10vfixture = dcsource.DCSource(devices['DCS1'])
        self.dcs_5v = dcsource.DCSource(devices['DCS2'])
        self.dcl_24v = dcload.DCLoad(devices['DCL1'])
        self.dcl_12v = dcload.DCLoadParallel(
            ((dcload.DCLoad(devices['DCL2']), 12),
             (dcload.DCLoad(devices['DCL3']), 10)))
        self.dcl_5v = dcload.DCLoad(devices['DCL4'])
        self.rla_pson = relay.Relay(devices['RLA1'])     # ON == Enable unit
        self.rla_12v2off = relay.Relay(devices['RLA2'])  # ON == 12V2 off
        self.rla_boot = relay.Relay(devices['RLA3'])     # ON == Asserted
        self.rla_reset = relay.Relay(devices['RLA4'])    # ON == Asserted
        # Serial connection to the ARM console
        arm_ser = SimSerial(simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately - don't open until after programming
        arm_ser.port = limit.ARM_PORT
        self.arm = Console(arm_ser, verbose=False)

    def arm_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
            self.arm.puts(string_data, preflush, postflush, priority)

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
        # Switch off DC Loads
        self.loads(i5=0, i12=0, i24=0)
        # Switch off DC Source
        self.dcs_5v.output(0.0, False)
        # Switch off all Relays
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
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.mirarm = sensor.Mirror()
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
        self.arm_acfreq = con_sensor(d.arm, 'AcFreq')
        self.arm_acvolt = con_sensor(d.arm, 'AcVolt')
        self.arm_5v = con_sensor(d.arm, '5V')
        self.arm_12v = con_sensor(d.arm, '12V')
        self.arm_24v = con_sensor(d.arm, '24V')
        self.arm_swver = con_sensor(
            d.arm, 'SwVer', rdgtype=sensor.ReadingString)
        self.arm_swbld = con_sensor(
            d.arm, 'SwBld', rdgtype=sensor.ReadingString)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensor."""
        self.mirarm.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.lock)
        self.dmm_part = Measurement(limits['PartCheck'], sense.part)
        self.dmm_fanshort = Measurement(limits['FanShort'], sense.fanshort)
        self.pgmarm = Measurement(limits['Program'], sense.mirarm)
        self.dmm_acin = Measurement(limits['InputFuse'], sense.acin)
        self.dmm_12vpri = Measurement(limits['12Vpri'], sense.o12vpri)
        self.dmm_5vset = Measurement(limits['5Vset'], sense.o5v)
        self.dmm_5v = Measurement(limits['5V'], sense.o5v)
        self.dmm_12voff = Measurement(limits['12Voff'], sense.o12v)
        self.dmm_12vpre = Measurement(limits['12Vpre'], sense.o12v)
        self.dmm_12vset = Measurement(limits['12Vset'], sense.o12v)
        self.dmm_12v = Measurement(limits['12V'], sense.o12v)
        self.dmm_12v2off = Measurement(limits['12V2off'], sense.o12v2)
        self.dmm_12v2pre = Measurement(limits['12V2pre'], sense.o12v2)
        self.dmm_12v2 = Measurement(limits['12V2'], sense.o12v2)
        self.dmm_24voff = Measurement(limits['24Voff'], sense.o24v)
        self.dmm_24vpre = Measurement(limits['24Vpre'], sense.o24v)
        self.dmm_24v = Measurement(limits['24V'], sense.o24v)
        self.dmm_vdsfet = Measurement(limits['VdsQ103'], sense.vdsfet)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3v3)
        self.dmm_pfcpre = Measurement(limits['PFCpre'], sense.pfc)
        self.dmm_pfcpost1 = Measurement(limits['PFCpost1'], sense.pfc)
        limits['PFCpost1'].position_fail = False
        self.dmm_pfcpost2 = Measurement(limits['PFCpost2'], sense.pfc)
        limits['PFCpost2'].position_fail = False
        self.dmm_pfcpost3 = Measurement(limits['PFCpost3'], sense.pfc)
        limits['PFCpost3'].position_fail = False
        self.dmm_pfcpost4 = Measurement(limits['PFCpost4'], sense.pfc)
        limits['PFCpost4'].position_fail = False
        self.dmm_pfcpost = Measurement(limits['PFCpost'], sense.pfc)
        self.dmm_pwrfail = Measurement(limits['PwrFail'], sense.pwrfail)
        self.arm_acfreq = Measurement(limits['ARM-AcFreq'], sense.arm_acfreq)
        self.arm_acvolt = Measurement(limits['ARM-AcVolt'], sense.arm_acvolt)
        self.arm_5v = Measurement(limits['ARM-5V'], sense.arm_5v)
        self.arm_12v = Measurement(limits['ARM-12V'], sense.arm_12v)
        self.arm_24v = Measurement(limits['ARM-24V'], sense.arm_24v)
        self.arm_swver = Measurement(limits['SwVer'], sense.arm_swver)
        self.arm_swbld = Measurement(limits['SwBld'], sense.arm_swbld)
