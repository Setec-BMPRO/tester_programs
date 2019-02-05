#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Final Test Program."""

import tester
from tester import LimitBoolean, LimitRegExp
import share
from . import config


class Final(share.TestSequence):

    """RVSWT101 Final Test Program."""

    limitdata = (
        LimitRegExp('BleMac', '^[0-9a-f]{12}$', doc='Valid MAC address'),
        LimitBoolean('ScanMac', True, doc='MAC address detected'),
        LimitBoolean('ButtonOk', True, doc='Ok entered'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None
        self.serialtomac = config.SerialToMAC()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        # Lookup the MAC address from the server
        mac = self.serialtomac.blemac_get(self.sernum)
        mes['ble_mac'].sensor.store(mac)
        mes['ble_mac']()
        # Tell user to push unit's button after clicking OK
        mes['ui_buttonpress']()
        # Scan for the RVSWT101 bluetooth transmission
        reply = dev['pi_bt'].scan_advert_blemac(mac)
        mes['scan_mac'].sensor.store(reply)
        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()

    def reset(self):
        """Reset instruments."""
        pass

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
            ))
