#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RVVIEW Initial Test Program."""

import os
import inspect
import tester
from tester import (
    TestStep,
    LimitLo, LimitBoolean, LimitString,
    LimitHiLo, LimitHiLoPercent, LimitHiLoInt
    )
import share
from . import console

BIN_VERSION = '1.0.14022.985'   # Software binary version
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
ARM_HW_VER = (2, 0, 'A')
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# Software image filename
ARM_FILE = 'RvView_{0}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'
# Input voltage to power the unit
VIN_SET = 8.1
# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

LIMITS = (
    LimitHiLo('Vin', (7.0, 8.0)),
    LimitHiLoPercent('3V3', (3.3, 3.0)),
    LimitLo('BkLghtOff', 0.5),
    LimitHiLo('BkLghtOn', (2.5, 3.5)),
    LimitString('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    LimitString('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    LimitString('CAN_RX', r'^RRQ,32,0'),
    LimitHiLoInt('CAN_BIND', _CAN_BIND),
    LimitBoolean('Notify', True),
    )


class Initial(share.TestSequence):

    """RVVIEW Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep(
                'Program', self.devices['programmer'].program, not self.fifo),
            TestStep('Initialise', self._step_initialise),
            TestStep('Display', self._step_display),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_SnEntry')
        dev['dcs_vin'].output(VIN_SET, True)
        self.measure(('dmm_vin', 'dmm_3V3'), timeout=5)

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the ARM device.

        Reset the device, set HW version & Serial number.

        """
        rvview = dev['rvview']
        rvview.open()
        rvview.brand(ARM_HW_VER, self.sernum, dev['rla_reset'])
        mes['arm_swver']()

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD.

        Put device into test mode.
        Check all segments and backlight.

        """
        rvview = dev['rvview']
        rvview.testmode(True)
        self.measure(
            ('ui_YesNoOn', 'dmm_BkLghtOn', 'ui_YesNoOff', 'dmm_BkLghtOff'),
            timeout=5)
        rvview.testmode(False)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        rvview = dev['rvview']
        mes['arm_can_bind'](timeout=10)
        rvview.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        rvview['CAN'] = CAN_ECHO
        echo_reply = dev['rvview_ser'].readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        rx_can = mes['rx_can']
        rx_can.sensor.store(echo_reply)
        rx_can()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        file = os.path.join(
            os.path.dirname(
                os.path.abspath(inspect.getfile(inspect.currentframe()))),
            ARM_FILE)
        self['programmer'] = share.ProgramARM(
            ARM_PORT, file, crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the rvview console
        self['rvview_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['rvview_ser'].port = ARM_PORT
        # rvview Console driver
        self['rvview'] = console.DirectConsole(
            self['rvview_ser'], verbose=False)
        # Power to fixture Comms circuits.
        self['dcs_vcom'].output(9.0, True)

    def reset(self):
        """Reset instruments."""
        self['rvview'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()

    def close(self):
        """Finished testing."""
        self['dcs_vcom'].output(0, False)
        super().close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        rvview = self.devices['rvview']
        sensor = tester.sensor
        self['mir_can'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['oBkLght'] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('rvview_initial', 'msgSnEntry'),
            caption=tester.translate('rvview_initial', 'capSnEntry'),
            timeout=300)
        self['oYesNoOn'] = sensor.YesNo(
            message=tester.translate('rvview_initial', 'PushButtonOn?'),
            caption=tester.translate('rvview_initial', 'capButtonOn'))
        self['oYesNoOff'] = sensor.YesNo(
            message=tester.translate('rvview_initial', 'PushButtonOff?'),
            caption=tester.translate('rvview_initial', 'capButtonOff'))
        self['arm_canbind'] = console.Sensor(rvview, 'CAN_BIND')
        self['oSwVer'] = console.Sensor(
            rvview, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        for measurement_name, limit_name, sensor_name in (
                ('dmm_vin', 'Vin', 'oVin'),
                ('dmm_3V3', '3V3', 'o3V3'),
                ('dmm_BkLghtOff', 'BkLghtOff', 'oBkLght'),
                ('dmm_BkLghtOn', 'BkLghtOn', 'oBkLght'),
                ('ui_SnEntry', 'SerNum', 'oSnEntry'),
                ('arm_swver', 'SwVer', 'oSwVer'),
                ('rx_can', 'CAN_RX', 'mir_can'),
                ('arm_can_bind', 'CAN_BIND', 'arm_canbind'),
                ('ui_YesNoOn', 'Notify', 'oYesNoOn'),
                ('ui_YesNoOff', 'Notify', 'oYesNoOff'),
            ):
            self[measurement_name] = tester.Measurement(
                self.limits[limit_name], self.sensors[sensor_name])