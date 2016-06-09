#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import inspect

import tester
import share
import sensor
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        # Power RS232 + Fixture Trek2.
        self.dcs_Vcom = tester.DCSource(devices['DCS1'])
        self.dcs_Vin = tester.DCSource(devices['DCS2'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = share.ProgramARM(
            limit.ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the Trek2 console
        self.trek2_ser = share.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.trek2_ser.port = limit.ARM_PORT
        # Trek2 Console driver
        self.trek2 = console.DirectConsole(self.trek2_ser)

    def trek2_puts(self,
                   string_data, preflush=0, postflush=0, priority=False,
                   addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.trek2.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.trek2.close()
        self.dcs_Vin.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        trek2 = logical_devices.trek2
        self.oMirCAN = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oBkLght = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('trek2_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_initial', 'capSnEntry'),
            timeout=300)
        self.oCANBIND = console.Sensor(trek2, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            trek2, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.rx_can = Measurement(limits['CAN_RX'], sense.oMirCAN)
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_BkLghtOff = Measurement(limits['BkLghtOff'], sense.oBkLght)
        self.dmm_BkLghtOn = Measurement(limits['BkLghtOn'], sense.oBkLght)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.trek2_can_bind = Measurement(limits['CAN_BIND'], sense.oCANBIND)
        self.trek2_SwVer = Measurement(limits['SwVer'], sense.oSwVer)
