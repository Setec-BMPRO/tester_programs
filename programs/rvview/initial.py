#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RVVIEW Initial Test Program."""

import os
import inspect
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitBetween, LimitPercent, LimitInteger
    )
import share
from . import console


class Initial(share.TestSequence):

    """RVVIEW Initial Test Program."""

    bin_version = '1.0.14022.985'   # Software binary version
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    arm_hw_ver = (2, 0, 'A')
    # Serial port for the ARM. Used by programmer and ARM comms module.
    arm_port = share.port('029687', 'ARM')
    # Software image filename
    arm_file = 'RvView_{0}.bin'.format(bin_version)
    # CAN echo request messages
    can_echo = 'TQQ,32,0'
    # Input voltage to power the unit
    vin_set = 8.1
    # CAN Bus is operational if status bit 28 is set
    _can_bind = 1 << 28

    limitdata = (
        LimitBetween('Vin', 7.0, 8.0),
        LimitPercent('3V3', 3.3, 3.0),
        LimitLow('BkLghtOff', 0.5),
        LimitBetween('BkLghtOn', 2.5, 3.5),
        LimitRegExp('SwVer', '^{0}$'.format(bin_version.replace('.', r'\.'))),
        LimitRegExp('CAN_RX', r'^RRQ,32,0'),
        LimitInteger('CAN_BIND', _can_bind),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self.devices['programmer'].program),
            TestStep('Initialise', self._step_initialise),
            TestStep('Display', self._step_display),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_SnEntry')
        dev['dcs_vin'].output(self.vin_set, True)
        self.measure(('dmm_vin', 'dmm_3V3'), timeout=5)

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the ARM device.

        Reset the device, set HW version & Serial number.

        """
        rvview = dev['rvview']
        rvview.open()
        rvview.brand(self.arm_hw_ver, self.sernum, dev['rla_reset'])
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
        rvview['CAN'] = self.can_echo
        echo_reply = rvview.port.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        rx_can = mes['rx_can']
        rx_can.sensor.store(echo_reply)
        rx_can()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
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
            Initial.arm_file)
        self['programmer'] = share.ProgramARM(
            Initial.arm_port, file, crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the rvview console
        rvview_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        rvview_ser.port = Initial.arm_port
        # rvview Console driver
        self['rvview'] = console.DirectConsole(rvview_ser)
        # Power to fixture Comms circuits.
        self['dcs_vcom'].output(9.0, True)
        self.add_closer(lambda: self['dcs_vcom'].output(0, False))

    def reset(self):
        """Reset instruments."""
        self['rvview'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


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
        self.create_from_names((
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_BkLghtOff', 'BkLghtOff', 'oBkLght', ''),
            ('dmm_BkLghtOn', 'BkLghtOn', 'oBkLght', ''),
            ('ui_SnEntry', 'SerNum', 'oSnEntry', ''),
            ('arm_swver', 'SwVer', 'oSwVer', ''),
            ('rx_can', 'CAN_RX', 'mir_can', ''),
            ('arm_can_bind', 'CAN_BIND', 'arm_canbind', ''),
            ('ui_YesNoOn', 'Notify', 'oYesNoOn', ''),
            ('ui_YesNoOff', 'Notify', 'oYesNoOff', ''),
            ))
