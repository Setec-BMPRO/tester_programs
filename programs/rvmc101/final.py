#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101x Final Test Program."""

import tester

import share

from . import device


class Final(share.TestSequence):

    """RVMC101x Final Test Program."""

    limitdata = (
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('CanBus', self._step_canbus),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev['dcs_vin'].output(12.0, output=True, delay=0.5)

    @share.teststep
    def _step_display(self, dev, mes):
        """Check all 7-segment displays."""
        mes['ui_yesnodisplay']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        candev = dev['can']
        candev.flush_can()
        try:
            packet = candev.read_can()
# FIXME: Add button testing by reading the CAN packets
#            rvmc_packet = device.Packet(packet)
            result = True
        except tester.devphysical.can.SerialToCanError:
            result = False
        mes['can_active'].sensor.store(result)
        mes['can_active']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dcs_vin', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = True
        self.add_closer(self.close_can)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)

    def close_can(self):
        """Restore CAN interface to default settings."""
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['MirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['yesnodisplay'] = sensor.YesNo(
            message=tester.translate('rvmc101_initial', 'DisplaysOn?'),
            caption=tester.translate('rvmc101_initial', 'capDisplay'))
        self['yesnodisplay'].doc = 'Tester operator'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('can_active', 'CANok', 'MirCAN', 'CAN bus traffic seen'),
            ('ui_yesnodisplay', 'Notify', 'yesnodisplay', 'Check display'),
            ))
