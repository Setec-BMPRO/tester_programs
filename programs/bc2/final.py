#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitDelta, LimitBoolean, LimitRegExp
    )
import share


class Final(share.TestSequence):

    """BC2 Final Test Program."""

    arm_version = '1.2.14549.989'
    limits = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('Shunt', 50.0, 100.0),
        LimitRegExp('SerNum', '^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
        LimitBoolean('Notify', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limits, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Bluetooth', self._step_bluetooth),
            TestStep('Cal', self._step_cal),
            )
        self.sernum = None

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes['ui_sernum'])
        self.measure(('dmm_vin', ), timeout=5)
        btmac = ''
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        if self.fifo:
            reply = True
        else:
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


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    # Test fixture item number
    fixture = '030451'

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('acsource', tester.ACSource, 'ACS'),
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the BLE module
        self['ble_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        self['ble_ser'].port = share.port(self.fixture, 'BLE')
        self['ble'] = share.BleRadio(self['ble_ser'])
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