#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Test Program."""

import time
from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from . import console

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])
        self.dcs_3v3 = dcsource.DCSource(devices['DCS2'])
        self.dcs_out = dcsource.DCSource(devices['DCS3'])
        self.dcl = dcload.DCLoad(devices['DCL1'])
        self.rla_reset = relay.Relay(devices['RLA1'])   # ON == Asserted
        self.rla_boot = relay.Relay(devices['RLA2'])    # ON == Asserted
        self.rla_outrev = relay.Relay(devices['RLA3'])    # ON == Asserted

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        self.dcl.output(0.0, False)
        for dcs in (self.dcs_vcom, self.dcs_3v3, self.dcs_out):
            dcs.output(0.0, output=False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_outrev):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, bc15):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirARM = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.olock = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self.ofanshort = sensor.Res(dmm, high=13, low=6, rng=10000, res=1)
        self.oACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.o14Vpri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self.o12Vs = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o5Vs = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.ofan = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.o15Vs = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oVout = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=14.0, stop=17.0, step=0.25, delay=0.1)
        self.arm_swver = console.Sensor(
            bc15, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_vout = console.Sensor(
            bc15, 'not-pulsing-volts', scale=0.001)
        self.arm_iout = console.Sensor(
            bc15, 'not-pulsing-current', scale=0.001)
        self.arm_switch = console.Sensor(bc15, 'SWITCH')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirARM.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmARM = Measurement(limits['Program'], sense.oMirARM)
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_fanshort = Measurement(limits['FanShort'], sense.ofanshort)
        self.dmm_acin = Measurement(limits['ACin'], sense.oACin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.oVbus)
        self.dmm_14Vpri = Measurement(limits['14Vpri'], sense.o14Vpri)
        self.dmm_12Vs = Measurement(limits['12Vs'], sense.o12Vs)
        self.dmm_5Vs = Measurement(limits['5Vs'], sense.o5Vs)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_fanon = Measurement(limits['FanOn'], sense.ofan)
        self.dmm_fanoff = Measurement(limits['FanOff'], sense.ofan)
        self.dmm_15Vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_vout_cal = Measurement(limits['VoutCal'], sense.oVout)
        self.dmm_voutoff = Measurement(limits['VoutOff'], sense.oVout)
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.arm_swver)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.arm_vout)
        self.arm_2amp = Measurement(limits['ARM-2amp'], sense.arm_iout)
        self.arm_2amp_lucky = Measurement(
            limits['ARM-2amp-Lucky'], sense.arm_iout)
        self.arm_switch = Measurement(limits['ARM-switch'], sense.arm_switch)
        self.arm_14amp = Measurement(limits['ARM-14amp'], sense.arm_iout)
