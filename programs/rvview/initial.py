#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""RVVIEW Initial Test Program."""

import os
import inspect
import tester
from tester.testlimit import (
    lim_hilo_percent, lim_hilo_int, lim_hilo,
    lim_lo, lim_string, lim_boolean)
import share
from share import oldteststep
from . import console

BIN_VERSION = '1.0.14022.985'   # Software binary version
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
ARM_HW_VER = (2, 0, 'A')

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# Software image filename
ARM_BIN = 'RvView_{}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'
# Input voltage to power the unit
VIN_SET = 8.1

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

LIMITS = tester.testlimit.limitset((
    lim_hilo('Vin', 7.0, 8.0),
    lim_hilo_percent('3V3', 3.3, 3.0),
    lim_lo('BkLghtOff', 0.5),
    lim_hilo('BkLghtOn', 2.5, 3.5),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_string('CAN_RX', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_boolean('Notify', True),
    ))


class Initial(tester.TestSequence):

    """RVVIEW Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.limits = LIMITS
        self.logdev = LogicalDevices(self.physical_devices, self.fifo)
        self.sensors = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensors, self.limits)
        # Power to fixture Comms circuits.
        self.logdev.dcs_vcom.output(9.0, True)
        self.sernum = None

    def close(self):
        """Finished testing."""
        self.logdev.dcs_vcom.output(0.0, False)
        self.logdev = None
        self.sensors = None
        self.meas = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_SnEntry)
        dev.dcs_vin.output(VIN_SET, True)
        tester.MeasureGroup((mes.dmm_vin, mes.dmm_3V3), timeout=5)

    @oldteststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev.programmer.program()

    @oldteststep
    def _step_initialise(self, dev, mes):
        """Initialise the ARM device.

        Reset the device, set HW version & Serial number.

        """
        dev.rvview.open()
        dev.rvview.brand(ARM_HW_VER, self.sernum, dev.rla_reset)
        mes.arm_swver.measure()

    @oldteststep
    def _step_display(self, dev, mes):
        """Test the LCD.

        Put device into test mode.
        Check all segments and backlight.

        """
        dev.rvview.testmode(True)
        tester.MeasureGroup(
            (mes.ui_YesNoOn, mes.dmm_BkLghtOn, mes.ui_YesNoOff,
             mes.dmm_BkLghtOff),
            timeout=5)
        dev.rvview.testmode(False)

    @oldteststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes.arm_can_bind.measure(timeout=10)
        dev.rvview.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        dev.rvview['CAN'] = CAN_ECHO
        echo_reply = dev.rvview_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()


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
            ARM_BIN)
        self.programmer = share.ProgramARM(ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the rvview console
        self.rvview_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.rvview_ser.port = ARM_PORT
        # rvview Console driver
        self.rvview = console.DirectConsole(self.rvview_ser, verbose=False)

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
