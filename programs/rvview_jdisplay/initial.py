#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay Initial Test Program."""

import pathlib

import serial
import tester

import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RvView/JDisplay Initial Test Program."""

    # Input voltage to power the unit
    vin_set = 8.1
    # Common limits
    _common = (
        tester.LimitBetween('Vin', 7.0, 8.0, doc='Input voltage present'),
        tester.LimitPercent('3V3', 3.3, 3.0, doc='3V3 present'),
        tester.LimitLow('BkLghtOff', 0.5, doc='Backlight off'),
        tester.LimitBetween('BkLghtOn', 2.5, 3.5, doc='Backlight on'),
        # CAN Bus is operational if status bit 28 is set
        tester.LimitInteger('CAN_BIND', 1 << 28, doc='CAN bus bound'),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        'JD': {
            'Config': config.JDisplay,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.JDisplay.sw_version.replace('.', r'\.'))),
                ),
            },
        'RV': {
            'Config': config.RvView,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.RvView.sw_version.replace('.', r'\.'))),
                ),
            },
        'RV2': {
            'Config': config.RvView2,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.RvView2.sw_version.replace('.', r'\.'))),
                ),
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        self.config = self.config_data[self.parameter]['Config']
        Devices.sw_file = self.config.sw_file
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('Initialise', self._step_initialise),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.vin_set, True)
        self.measure(('dmm_vin', 'dmm_3v3'), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM."""
        dev['programmer'].program()

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the ARM device.

        Reset the device, set HW version & Serial number.

        """
        arm = dev['arm']
        arm.open()
        arm.brand(self.config.hw_version, self.sernum, dev['rla_reset'])
        mes['sw_ver']()

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD.

        Put device into test mode.
        Check all segments and backlight.

        """
        arm = dev['arm']
        arm.testmode(True)
        self.measure(
            ('ui_yesnoon', 'dmm_bklghton', 'ui_yesnooff', 'dmm_bklghtoff'),
            timeout=5)
        arm.testmode(False)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['can_bind'](timeout=10)
        armtunnel = dev['armtunnel']
        armtunnel.open()
        mes['tunnel_swver']()
        armtunnel.close()


class Devices(share.Devices):

    """Devices."""

    sw_file = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_wd', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        arm_port = share.config.Fixture.port('029687', 'ARM')
        # ARM device programmer
        self['programmer'] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_file,
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset']
            )
        # Direct Console driver
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        # Console driver
        self['arm'] = console.DirectConsole(arm_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.rvview)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['armtunnel'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_wd'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        arm = self.devices['arm']
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['mir_can'] = sensor.MirrorReadingString()
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X1'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U1 output'
        self['bklght'] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self['bklght'].doc = 'Across backlight'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('rvview_jdisplay_initial', 'msgSnEntry'),
            caption=tester.translate('rvview_jdisplay_initial', 'capSnEntry'),
            timeout=300)
        self['sernum'].doc = 'Barcode scanner'
        self['oYesNoOn'] = sensor.YesNo(
            message=tester.translate(
            'rvview_jdisplay_initial', 'PushButtonOn?'),
            caption=tester.translate('rvview_jdisplay_initial', 'capButtonOn'))
        self['oYesNoOn'].doc = 'Operator input'
        self['oYesNoOff'] = sensor.YesNo(
            message=tester.translate(
            'rvview_jdisplay_initial', 'PushButtonOff?'),
            caption=tester.translate('rvview_jdisplay_initial', 'capButtonOff'))
        self['oYesNoOff'].doc = 'Operator input'
        # Console sensors
        self['canbind'] = sensor.KeyedReading(arm, 'CAN_BIND')
        self['swver'] = sensor.KeyedReadingString(arm, 'SW_VER')
        self['tunnelswver'] = sensor.KeyedReadingString(armtunnel, 'SW_VER')


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_bklghtoff', 'BkLghtOff', 'bklght', 'Test backlight'),
            ('dmm_bklghton', 'BkLghtOn', 'bklght', 'Test backlight'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('sw_ver', 'SwVer', 'swver', 'Unit software version'),
            ('ui_yesnoon', 'Notify', 'oYesNoOn', 'Button on'),
            ('ui_yesnooff', 'Notify', 'oYesNoOff', 'Button off'),
            ('can_bind', 'CAN_BIND', 'canbind', 'CAN bound'),
            ('tunnel_swver', 'SwVer', 'tunnelswver', 'Unit software version'),
            ))
