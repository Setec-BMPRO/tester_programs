#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Final Test Program."""

import tester

import share
from . import config, device


class Final(share.TestSequence):

    """RVSWT101 Final Test Program."""

    ble_adtype_manufacturer = 255

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter)
        super().open(self.cfg['limits_fin'], Devices, Sensors, Measurements)
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
        # Tell user to push unit's button after clicking OK
        mes['ui_buttonpress']()
        # Scan for the bluetooth transmission
        # Reply is like this: {
        #   'ad_data': {255: '1f050112022d624c3a00000300d1139e69'},
        #   'rssi': -80,
        #   }
        reply = dev['pi_bt'].scan_advert_blemac(mac, timeout=20)
        mes['scan_mac'].sensor.store(reply is not None)
        mes['scan_mac']()
        packet = reply['ad_data'][str(self.ble_adtype_manufacturer)]
        dev['decoder'].packet = device.Packet(packet)
        self.measure(('cell_voltage', 'switch_type', ))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        # BLE Packet decoder
        self['decoder'] = tester.CANPacket()


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
        self['ButtonPress'] = sensor.OkCan(
            message=tester.translate('rvswt101_final', 'msgPressButton'),
            caption=tester.translate('rvswt101_final', 'capPressButton'))
        decoder = self.devices['decoder']
        self['cell_voltage'] = tester.sensor.CANPacket(decoder, 'cell_voltage')
        self['switch_type'] = tester.sensor.CANPacket(decoder, 'switch_type')


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from server'),
            ('ui_buttonpress', 'ButtonOk', 'ButtonPress', ''),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ('cell_voltage', 'CellVoltage', 'cell_voltage',
                'Button cell charged'),
            ('switch_type', 'SwitchType', 'switch_type',
                'Switch type'),
            ))
