#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Initial Program."""

import tester
from tester import (
    TestStep,
    LimitDelta, LimitBoolean, LimitRegExp
    )
import share
from . import console


class Initial(share.TestSequence):

    """BC2 Initial Test Program."""

    arm_version = '1.2.14549.989'
    limitdata = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('3V3', 3.3, 0.25),
        LimitDelta('Shunt', 50.0, 100.0),
        LimitRegExp('ARM-SwVer',
            '^{}$'.format(arm_version.replace('.', r'\.'))),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(12.0, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=15.0)
        btmac = mes['bc2_btmac']().reading1
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        ble = dev['ble']
        ble.open()
        reply = ble.scan(btmac)
        ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        mes['detectBT'].sensor.store(reply)
        mes['detectBT']()


class Devices(share.Devices):

    """Devices."""

    # Test fixture item number
    fixture = '030451'

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_shunt', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_wdog', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        bc2_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bc2_ser.port = share.port(self.fixture, 'ARM')
        # Console driver
        self['bc2'] = console.Console(bc2_ser)
        # Serial connection to the BLE module
        ble_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.port(self.fixture, 'BLE')
        self['ble'] = share.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vin', 'dcs_shunt'):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdog', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['shunt'] = sensor.Vdc(
            dmm, high=3, low=1, rng=10, res=0.001, scale=1000)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        bc2 = self.devices['bc2']
        self['btmac'] = console.Sensor(
            bc2, 'BT_MAC', rdgtype=sensor.ReadingString)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_initial', 'msgSnEntry'),
            caption=tester.translate('bc2_initial', 'capSnEntry'))
        self['arm_swver'] = console.Sensor(
            bc2, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_shunt', 'Shunt', 'shunt', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('bc2_btmac', 'BtMac', 'btmac', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ))
