#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVVIEW Initial Test Program."""

import os
import inspect
import tester
import share
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
        self.dcs_vcom = tester.DCSource(devices['DCS1'])
        self.dcs_vin = tester.DCSource(devices['DCS2'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = share.ProgramARM(
            limit.ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the rvview console
        self.rvview_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.rvview_ser.port = limit.ARM_PORT
        # rvview Console driver
        self.rvview = console.DirectConsole(self.rvview_ser, verbose=False)
        # Auto add prompt to puts strings
        self.rvview.puts_prompt = '\r\n> '

    def reset(self):
        """Reset instruments."""
        self.rvview.close()
        self.dcs_vin.output(0.0, False)
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
        rvview = logical_devices.rvview
        sensor = tester.sensor
        self.mir_can = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oBkLght = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('rvview_initial', 'msgSnEntry'),
            caption=tester.translate('rvview_initial', 'capSnEntry'),
            timeout=300)
        self.oYesNoOn = sensor.YesNo(
            message=tester.translate('rvview_initial', 'PushButtonOn?'),
            caption=tester.translate('rvview_initial', 'capButtonOn'))
        self.oYesNoOff = sensor.YesNo(
            message=tester.translate('rvview_initial', 'PushButtonOff?'),
            caption=tester.translate('rvview_initial', 'capButtonOff'))
        self.arm_canbind = console.Sensor(rvview, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            rvview, 'SW_VER', rdgtype=sensor.ReadingString)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.mir_can.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_BkLghtOff = Measurement(limits['BkLghtOff'], sense.oBkLght)
        self.dmm_BkLghtOn = Measurement(limits['BkLghtOn'], sense.oBkLght)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.arm_swver = Measurement(limits['SwVer'], sense.oSwVer)
        self.rx_can = Measurement(limits['CAN_RX'], sense.mir_can)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.arm_canbind)
        self.ui_YesNoOn = Measurement(
            limits['Notify'], sense.oYesNoOn)
        self.ui_YesNoOff = Measurement(
            limits['Notify'], sense.oYesNoOff)
