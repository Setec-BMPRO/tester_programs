#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import os
import inspect

import share
import tester
import sensor
from . import limit
from .. import console


class LogicalDevices(object):

    """BatteryCheck Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS1'])  # Fixture power
        self.dcs_shunt = tester.DCSource(devices['DCS2'])  # Shunt signal
        self.rla_avr = tester.Relay(devices['RLA1'])   # Connect AVR programmer
        self.rla_reset = tester.Relay(devices['RLA2'])   # ARM/AVR RESET signal
        self.rla_boot = tester.Relay(devices['RLA3'])    # ARM/AVR BOOT signal
        self.rla_arm = tester.Relay(devices['RLA4'])     # ARM programming port
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = share.ProgramARM(limit.ARM_PGM, file, crpmode=False)
        # Serial connection to the console
        arm_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=2)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = limit.ARM_CON
        self.arm = console.Console(arm_ser)
        # Serial connection to the BT device
        self.btport = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        self.btport.port = limit.BT_PORT
        # BT Radio driver
        self.bt = share.BtRadio(self.btport)

    def arm_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.arm.puts(string_data, preflush, postflush, priority)

    def bt_puts(self,
                string_data, preflush=0, postflush=0, priority=False,
                addcrlf=True):
        """Push string data into the buffer only if FIFOs are enabled."""
        if self._fifo:
            if addcrlf:
                string_data = string_data + '\r\n'
            self.btport.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.arm.close()
        self.bt.close()
        for dcs in (self.dcs_input, self.dcs_shunt):
            dcs.output(0.0, output=False)
        for rla in (self.rla_avr, self.rla_reset,
                    self.rla_boot, self.rla_arm):
            rla.set_off()


class Sensors(object):

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        arm = logical_devices.arm
        self.ARMvolt = console.Sensor(arm, 'VOLTAGE')
        self.ARMcurr = console.Sensor(arm, 'CURRENT')
        self.ARMsoft = console.Sensor(
            arm, 'SW_VER', rdgtype=sensor.ReadingString)
        self.oMirAVR = sensor.Mirror()
        self.oMirBT = sensor.Mirror()
        self.oMirCurrErr = sensor.Mirror()
        self.o3V3 = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.reg5V = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.reg12V = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self.shunt = sensor.Vdc(
            dmm, high=3, low=1, rng=1, res=0.001, scale=-1250)
        self.relay = sensor.Res(dmm, high=2, low=2, rng=10000, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('batterycheck_initial', 'msgSnEntry'),
            caption=tester.translate('batterycheck_initial', 'capSnEntry'))


class Measurements(object):

    """BatteryCheck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.pgmAVR = Measurement(limits['PgmAVR'], sense.oMirAVR)
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
