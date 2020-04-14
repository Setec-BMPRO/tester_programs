#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 SETEC Pty Ltd
"""RVMD50 Final Test Program."""

import tester

import share
from . import config, console


class Final(share.TestSequence):

    """RVMD50 Final Test Program."""

    # Input voltage to power the unit
    vin_set = 12.0
    # Time to wait for CAN binding (sec)
    can_bind_time = 9

    limitdata = (
        tester.LimitRegExp('SwVer', '^{0}$'.format(
            config.RVMD50.sw_version.replace('.', r'\.'))),
        )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TunnelOpen', self._step_tunnel_open),
            tester.TestStep('Display', self._step_display),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(
            self.vin_set, output=True, delay=self.can_bind_time)
        self.send_preconditions(self.physical_devices['CAN'][0])

    @share.teststep
    def _step_tunnel_open(self, dev, mes):
        """Open console tunnel."""
        unit = dev['armtunnel']
        unit.open()
        unit.testmode(True)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display tests."""
        unit = dev['armtunnel']
        self.measure(('sw_ver', 'ui_yesnoseg', 'ui_yesnobklght', ))
        # Set unit internal Serial Number to match the outside label
        unit.set_sernum(self.sernum)

    @staticmethod
    def send_preconditions(serial2can):
        """Send a Preconditions packet (for Trek2)."""
        pkt = tester.devphysical.can.SETECPacket()
        msg = pkt.header.message
        msg.device_id = tester.devphysical.can.SETECDeviceID.bp35.value
        msg.msg_type = tester.devphysical.can.SETECMessageType.announce.value
        msg.data_id = tester.devphysical.can.SETECDataID.preconditions.value
        pkt.data.extend(b'\x00\x00')    # Dummy data
        serial2can.send('t{0}'.format(pkt))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.trek2)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['armtunnel'].close()
        self['dcs_vin'].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['yesnoseg'] = sensor.YesNo(
            message=tester.translate('rvview_jdisplay_final', 'AreSegmentsOn?'),
            caption=tester.translate('rvview_jdisplay_final', 'capSegments'))
        self['yesnoseg'].doc = 'Operator input'
        self['yesnobklght'] = sensor.YesNo(
            message=tester.translate('rvview_jdisplay_final', 'IsBacklightOk?'),
            caption=tester.translate('rvview_jdisplay_final', 'capBacklight'))
        self['yesnobklght'].doc = 'Operator input'
        self['swver'] = sensor.KeyedReadingString(armtunnel, 'SW_VER')
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('rvview_jdisplay_final', 'msgSnEntry'),
            caption=tester.translate('rvview_jdisplay_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('ui_yesnoseg', 'Notify', 'yesnoseg', 'Segment display'),
            ('ui_yesnobklght', 'Notify', 'yesnobklght', 'Backlight'),
            ('sw_ver', 'SwVer', 'swver', 'Unit software version'),
            ))
