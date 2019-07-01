#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Final Test Program."""

import tester

import share
from . import config


class Final(share.TestSequence):

    """RVMN101 Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter)
        self.limits = self.cfg.limits_final()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        # Lookup the MAC address from the server
        mac = dev['serialtomac'].blemac_get(self.sernum)
        mes['ble_mac'].sensor.store(mac)
        mes['ble_mac']()
        # Scan for the RVSWT101 bluetooth transmission
        packet = dev['pi_bt'].scan_advert_blemac(mac, timeout=20)
        # packet is like this:
        #   [[255, 'Manufacturer', '1f050112022d624c3a00000300d1139e69']]
        mes['scan_mac'].sensor.store(packet is not None)
        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['mirscan'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['mirmac'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvswt101_final', 'msgSnEntry'),
            caption=tester.translate('rvswt101_final', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from server'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ))
