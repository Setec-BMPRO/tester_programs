#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from .. import console

translate = tester.translate


class LogicalDevices(object):

    """BatteryCheck Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_input = dcsource.DCSource(devices['DCS1'])  # Fixture power
        self.dcs_shunt = dcsource.DCSource(devices['DCS2'])  # Shunt signal
        self.rla_avr = relay.Relay(devices['RLA1'])   # Connect AVR programmer
        self.rla_reset = relay.Relay(devices['RLA2'])   # ARM/AVR RESET signal
        self.rla_boot = relay.Relay(devices['RLA3'])    # ARM/AVR BOOT signal
        self.rla_arm = relay.Relay(devices['RLA4'])     # ARM programming port

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_input, self.dcs_shunt):
            dcs.output(0.0, output=False)
        # Switch off all Relays
        for rla in (self.rla_avr, self.rla_reset,
                    self.rla_boot, self.rla_arm):
            rla.set_off()

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()


class Sensors(object):

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices, armdev):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.ARMvolt = console.Sensor(armdev, 'VOLTAGE')
        self.ARMcurr = console.Sensor(armdev, 'CURRENT')
        self.ARMsoft = console.Sensor(
            armdev, 'SW_VER', rdgtype=sensor.ReadingString)
        self.oMirAVR = sensor.Mirror()
        self.oMirARM = sensor.Mirror()
        self.oMirBT = sensor.Mirror()
        self.oMirCurrErr = sensor.Mirror()
        self.o3V3 = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.reg5V = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.reg12V = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self.shunt = sensor.Vdc(
            dmm, high=3, low=1, rng=1, res=0.001, scale=-1250)
        self.relay = sensor.Res(dmm, high=2, low=2, rng=10000, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=translate('batterycheck_initial', 'msgSnEntry'),
            caption=translate('batterycheck_initial', 'capSnEntry'))


class Measurements(object):

    """BatteryCheck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.pgmAVR = Measurement(limits['PgmAVR'], sense.oMirAVR)
        self.pgmARM = Measurement(limits['PgmARM'], sense.oMirARM)
        self.detectBT = Measurement(limits['DetectBT'], sense.oMirBT)
        self.voltARM = Measurement(limits['ARM_Volt'], sense.ARMvolt)
        self.currARM = Measurement(limits['ARM_Curr'], sense.ARMcurr)
        self.softARM = Measurement(limits['ARM_SwVer'], sense.ARMsoft)
        self.currErr = Measurement(limits['Batt_Curr_Err'], sense.oMirCurrErr)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_reg5V = Measurement(limits['5VReg'], sense.reg5V)
        self.dmm_reg12V = Measurement(limits['12VReg'], sense.reg12V)
        self.dmm_shunt = Measurement(limits['shunt'], sense.shunt)
        self.dmm_relay = Measurement(limits['Relay'], sense.relay)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.BTscan = Measurement(limits['BTscan'], sense.oMirBT)
