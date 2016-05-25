#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program."""

from pydispatch import dispatcher
import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from share.console import Sensor as con_sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dmm = dmm.DMM(devices['DMM'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_10Vfixture = dcsource.DCSource(devices['DCS1'])
        self.dcs_5V = dcsource.DCSource(devices['DCS2'])
        self.dcl_24V = dcload.DCLoad(devices['DCL1'])
        _dcl_12V = dcload.DCLoad(devices['DCL2'])
        _dcl_12V2 = dcload.DCLoad(devices['DCL3'])
        self.dcl_12V = dcload.DCLoadParallel(((_dcl_12V, 12), (_dcl_12V2, 10)))
        self.dcl_5V = dcload.DCLoad(devices['DCL4'])
        self.rla_pson = relay.Relay(devices['RLA1'])    # ON == Enable unit
        self.rla_12v2off = relay.Relay(devices['RLA2'])  # ON == 12V2 off
        self.rla_boot = relay.Relay(devices['RLA3'])    # ON == Asserted
        self.rla_reset = relay.Relay(devices['RLA4'])   # ON == Asserted

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Loads
        for ld in (self.dcl_5V, self.dcl_12V, self.dcl_24V):
            ld.output(0.0)
        # Switch off DC Source
        for dcs in (self.dcs_5V, ):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_12v2off, self.rla_pson,
                    self.rla_reset, self.rla_boot):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, armdev):
        """Create all Sensor instances."""
        d = logical_devices
        dmm = d.dmm
        # Mirror sensor for Programming result logging
        self.oMirARM = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.o5V = sensor.Vdc(dmm, high=7, low=4, rng=10, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self.o12V2 = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self.o24V = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self.PWRFAIL = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.001)
        self.o12Vpri = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self.PFC = sensor.Vdc(dmm, high=3, low=3, rng=1000, res=0.001)
        self.ACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.GPO = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self.Lock = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self.Part = sensor.Res(dmm, high=10, low=5, rng=1000, res=0.01)
        self.FanShort = sensor.Res(dmm, high=13, low=7, rng=1000, res=0.1)
        self.oVdsfet = sensor.Vdc(dmm, high=14, low=8, rng=100, res=0.001)
        self.ARM_AcFreq = con_sensor(armdev, 'ARM-AcFreq')
        self.ARM_AcVolt = con_sensor(armdev, 'ARM-AcVolt')
        self.ARM_5V = con_sensor(armdev, 'ARM-5V')
        self.ARM_12V = con_sensor(armdev, 'ARM-12V')
        self.ARM_24V = con_sensor(armdev, 'ARM-24V')
        self.ARM_SwVer = con_sensor(
            armdev, 'ARM_SwVer', rdgtype=sensor.ReadingString)
        self.ARM_SwBld = con_sensor(
            armdev, 'ARM_SwBld', rdgtype=sensor.ReadingString)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensor."""
        self.oMirARM.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.Lock)
        self.dmm_Part = Measurement(limits['PartCheck'], sense.Part)
        self.dmm_FanShort = Measurement(limits['FanShort'], sense.FanShort)
        # Programming result
        self.pgmARM = Measurement(limits['Program'], sense.oMirARM)
        self.dmm_ACin = Measurement(limits['InputFuse'], sense.ACin)
        self.dmm_12Vpri = Measurement(limits['12Vpri'], sense.o12Vpri)
        self.dmm_5Vset = Measurement(limits['5Vset'], sense.o5V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V)
        self.dmm_12Vpre = Measurement(limits['12Vpre'], sense.o12V)
        self.dmm_12Vset = Measurement(limits['12Vset'], sense.o12V)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.dmm_12V2off = Measurement(limits['12V2off'], sense.o12V2)
        self.dmm_12V2pre = Measurement(limits['12V2pre'], sense.o12V2)
        self.dmm_12V2 = Measurement(limits['12V2'], sense.o12V2)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_24Vpre = Measurement(limits['24Vpre'], sense.o24V)
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_Vdsfet = Measurement(limits['VdsQ103'], sense.oVdsfet)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_PFCpre = Measurement(limits['PFCpre'], sense.PFC)
        self.dmm_PFCpost1 = Measurement(limits['PFCpost1'], sense.PFC)
        limits['PFCpost1'].position_fail = False
        self.dmm_PFCpost2 = Measurement(limits['PFCpost2'], sense.PFC)
        limits['PFCpost2'].position_fail = False
        self.dmm_PFCpost3 = Measurement(limits['PFCpost3'], sense.PFC)
        limits['PFCpost3'].position_fail = False
        self.dmm_PFCpost4 = Measurement(limits['PFCpost4'], sense.PFC)
        limits['PFCpost4'].position_fail = False
        self.dmm_PFCpost = Measurement(limits['PFCpost'], sense.PFC)
        self.dmm_PWRFAIL = Measurement(limits['PWRFAIL'], sense.PWRFAIL)
        self.arm_AcFreq = Measurement(limits['ARM-AcFreq'], sense.ARM_AcFreq)
        self.arm_AcVolt = Measurement(limits['ARM-AcVolt'], sense.ARM_AcVolt)
        self.arm_5V = Measurement(limits['ARM-5V'], sense.ARM_5V)
        self.arm_12V = Measurement(limits['ARM-12V'], sense.ARM_12V)
        self.arm_24V = Measurement(limits['ARM-24V'], sense.ARM_24V)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.ARM_SwVer)
        self.arm_SwBld = Measurement(limits['ARM-SwBld'], sense.ARM_SwBld)
