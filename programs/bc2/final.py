#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Final Program."""

import serial
import tester
from tester import (
    TestStep,
    LimitDelta, LimitBoolean, LimitRegExp
    )
import share


class Final(share.TestSequence):

    """BC2 Final Test Program."""

    limitdata = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('Shunt', 50.0, 100.0),
        LimitRegExp('BtMac', share.bluetooth.MAC.line_regex),
        LimitBoolean('DetectBT', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Bluetooth', self._step_bluetooth),
            TestStep('Cal', self._step_cal),
            )
        self.sernum = None

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(('dmm_vin', ), timeout=5)
# FIXME: Where do we get the MAC from?
        btmac = '001EC030BC15'
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        ble = dev['ble']
        ble.open()
        reply = ble.scan(btmac)
        ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        mes['detectBT'].sensor.store(reply)
        mes['detectBT']()

    @share.teststep
    def _step_cal(self, dev, mes):
        """Prepare to run a test."""


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('acsource', tester.ACSource, 'ACS'),
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=5.0, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.fixture.port('030451', 'BLE')
        self['ble'] = share.bluetooth.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))
        self['acsource'].output(voltage=240.0, output=True)
        self.add_closer(lambda: self['acsource'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['shunt'] = sensor.Vdc(
            dmm, high=3, low=1, rng=10, res=0.001, scale=1000)
        self['mirbt'] = sensor.Mirror()
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_initial', 'msgSnEntry'),
            caption=tester.translate('bc2_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_shunt', 'Shunt', 'shunt', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ))
