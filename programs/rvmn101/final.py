#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Final Test Program."""

import tester

import share
from . import config


class Final(share.TestSequence):

    """RVMN101 and RVMN5x Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
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
        dev['dcs_vin'].output(self.cfg.vbatt_set, True, delay=2.0)
        # Lookup the MAC address from the server
        mac = dev['serialtomac'].blemac_get(self.sernum)
        mes['ble_mac'].sensor.store(mac)
        mes['ble_mac']()
        # Scan for the bluetooth transmission
        # Reply is like this: {
        #   'ad_data': {255: '1f050112022d624c3a00000300d1139e69'},
        #   'rssi': rssi,
        #   }
        reply = dev['pi_bt'].scan_advert_blemac(mac, timeout=20)
        mes['scan_mac'].sensor.store(reply is not None)
        mes['scan_mac']()
        rssi = reply['rssi']    # Received Signal Strength Indication
        mes['scan_rssi'].sensor.store(rssi)
        mes['scan_rssi']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        self['dcs_vin'] = tester.DCSource(self.physical_devices['DCS1'])

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvmn101_final', 'msgSnEntry'),
            caption=tester.translate('rvmn101_final', 'capSnEntry'))
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['mirmac'] = sensor.MirrorReadingString()
        self['mirrssi'] = sensor.MirrorReading()


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from server'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over Bluetooth'),
            ('scan_rssi', 'ScanRSSI', 'mirrssi', 'Bluetooth signal strength'),
            ))
