#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""TRS2 Final Program."""

import tester

import share


class Final(share.TestSequence):

    """TRS2 Final Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        tester.LimitDelta('Vin', vbatt, 0.5, doc='Input voltage present'),
        tester.LimitBoolean('ScanSer', True, doc='Serial number detected'),
        )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.vbatt, True)
        mes['dmm_vin'](timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self._logger.debug(
                'Scan for serial number via bluetooth: "%s"', self.sernum)
        reply = dev['pi_bt'].scan_beacon_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply)
        mes['scan_ser']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self['vin'].doc = 'Within Fixture'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trs2_final', 'msgSnEntry'),
            caption=tester.translate('trs2_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        self['mirscan'] = sensor.MirrorReadingBoolean()


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ))
