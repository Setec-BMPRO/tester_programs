#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Initial Program."""

import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitDelta, LimitPercent, LimitBoolean, LimitRegExp
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """TRSRFM Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        LimitDelta('Vin', 12.0, 0.5, doc='Input voltage present'),
        LimitPercent('3V3', 3.3, 0.5, doc='3V3 present'),
        LimitHigh('RedLedOff', 3.1, doc='Led off'),
        LimitDelta('RedLedOn', 0.5, 0.1, doc='Led on'),
        LimitHigh('GreenLedOff', 3.1, doc='Led off'),
        LimitLow('GreenLedOn', 0.2, doc='Led on'),
        LimitHigh('BlueLedOff', 3.1, doc='Led off'),
        LimitDelta('BlueLedOn', 0.3, 0.09, doc='Led on'),
        LimitLow('TestPinCover', 0.5, doc='Cover in place'),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$', doc='Valid MAC address'),
        LimitBoolean('DetectBT', True, doc='MAC address detected'),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('TestArm', self._step_test_arm),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        mes['dmm_tstpincov'](timeout=5)
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the operation of TRSRFM."""
        trsrfm = dev['trsrfm']
        trsrfm.open()
        trsrfm.brand(config.HW_VERSION, self.sernum)
        self.measure(
            ('arm_swver', 'dmm_redoff', 'dmm_greenoff', 'dmm_blueoff'),
            timeout=5)
        trsrfm.override(share.Override.force_on)
        self.measure(
            ('dmm_redon', 'dmm_greenon', 'dmm_blueon'), timeout=5)
        trsrfm.override(share.Override.force_off)
        self.measure(
            ('dmm_redoff', 'dmm_greenoff', 'dmm_blueoff'), timeout=5)
        trsrfm.override(share.Override.normal)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        btmac = mes['arm_btmac']().reading1
        dev['dcs_vin'].output(0.0, True, delay=3.0)
        dev['rla_pair_btn'].set_on(delay=0.1)
        dev['dcs_vin'].output(self.vbatt, True, delay=5.0)
        dev['rla_pair_btn'].set_off()
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

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_wdog', tester.Relay, 'RLA2'),
                ('rla_pair_btn', tester.Relay, 'RLA8'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        trsrfm_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        trsrfm_ser.port = share.port('030451', 'ARM')
        # Console driver
        self['trsrfm'] = console.Console(trsrfm_ser)
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.port('030451', 'BLE')
        self['ble'] = share.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['trsrfm'].close()
        for dev in ('dcs_vin', ):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdog', 'rla_pair_btn'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'Across X1-X2'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U2 output'
        self['red'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self['red'].doc = 'Led cathode'
        self['green'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self['green'].doc = 'Led cathode'
        self['blue'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self['blue'].doc = 'Led cathode'
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['tstpin_cover'].doc = 'Photo sensor'
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        trsrfm = self.devices['trsrfm']
        for name, cmdkey in (
                ('arm_BtMAC', 'BT_MAC'),
                ('arm_SwVer', 'SW_VER'),
            ):
            self[name] = console.Sensor(
                trsrfm, cmdkey, rdgtype=sensor.ReadingString)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trsrfm_initial', 'msgSnEntry'),
            caption=tester.translate('trsrfm_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_redoff', 'RedLedOff', 'red', 'Red led off'),
            ('dmm_redon', 'RedLedOn', 'red', 'Red led on'),
            ('dmm_greenoff', 'GreenLedOff', 'green', 'Green led off'),
            ('dmm_greenon', 'GreenLedOn', 'green', 'Green led on'),
            ('dmm_blueoff', 'BlueLedOff', 'blue', 'Blue led off'),
            ('dmm_blueon', 'BlueLedOn', 'blue', 'Blue led on'),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover',
                'Cover over BC2 test pins'),
            ('arm_btmac', 'BtMac', 'arm_BtMAC', 'MAC address'),
            ('detectBT', 'DetectBT', 'mirbt', 'Scanned MAC address'),
            ('arm_swver', 'ARM-SwVer', 'arm_SwVer', 'Unit software version'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ))
