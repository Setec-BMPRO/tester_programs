#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Initial Program."""

import tester
from tester import (
    TestStep, LimitLow, LimitHigh, LimitDelta, LimitBoolean, LimitRegExp
    )
import share
from . import console


class Initial(share.TestSequence):

    """TRSRFM Initial Test Program."""

    arm_version = '1.2.14549.989'
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_ver = (5, 0, 'B')
    # Injected Vbatt
    vbatt = 12.0
    #Manual override parameters
    force_on = 2
    force_off = 1
    normal = 0
    # Test limits
    limitdata = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('3V3', 3.3, 0.25),
        LimitHigh('RedLedOff', 3.1),
        LimitDelta('RedLedOn', 0.5, 0.1),
        LimitHigh('GreenLedOff', 3.1),
        LimitLow('GreenLedOn', 0.14),
        LimitHigh('BlueLedOff', 3.1),
        LimitDelta('BlueLedOn', 0.25, 0.1),
        LimitDelta('BlueLedFlash', 1.65, 0.2),
        LimitLow('TestPinCover', 0.5),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(arm_version.replace('.', r'\.'))),
        LimitLow('ARM-FltCode', 0),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
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
        dev['rla_reset'].pulse(0.1)
        trsrfm.action(None, delay=5.0, expected=2)  # Flush banner
        trsrfm['HW_VER'] = self.hw_ver
        trsrfm['SER_ID'] = self.sernum
        trsrfm['NVDEFAULT'] = True
        trsrfm['NVWRITE'] = True
        mes['arm_swver']()
        mes['arm_fltcode']()
        self.measure(
            ('dmm_redoff', 'dmm_greenoff', 'dmm_blueflash'), timeout=5)
        trsrfm.override(self.force_on)
        self.measure(
            ('dmm_redon', 'dmm_greenon', 'dmm_blueon'), timeout=5)
        trsrfm.override(self.force_off)
        self.measure(
            ('dmm_redoff', 'dmm_greenoff', 'dmm_blueoff'), timeout=5)
        trsrfm.override(self.normal)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(self.vbatt, delay=15.0)
        btmac = mes['trsrfm_btmac']().reading1
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

    arm_port = share.port('030451', 'ARM')
    ble_port = share.port('030451', 'BLE')

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
                ('rla_pin', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        trsrfm_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        trsrfm_ser.port = self.arm_port
        # Console driver
        self['trsrfm'] = console.Console(trsrfm_ser)
        # Serial connection to the BLE module
        ble_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = self.ble_port
        self['ble'] = share.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vin', ):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdog', 'rla_pin'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['red'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self['green'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self['blue'] = sensor.Vdc(
            dmm, high=7, low=1, rng=10, res=0.01, nplc=10)
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        trsrfm = self.devices['trsrfm']
        self['btmac'] = console.Sensor(
            trsrfm, 'BT_MAC', rdgtype=sensor.ReadingString)
        self['arm_swver'] = console.Sensor(
            trsrfm, 'SW_VER', rdgtype=sensor.ReadingString)
        self['arm_fltcode'] = console.Sensor(
            trsrfm, 'FAULT_CODE')
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trsrfm_initial', 'msgSnEntry'),
            caption=tester.translate('trsrfm_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_redoff', 'RedLedOff', 'red', ''),
            ('dmm_redon', 'RedLedOn', 'red', ''),
            ('dmm_greenoff', 'GreenLedOff', 'green', ''),
            ('dmm_greenon', 'GreenLedOn', 'green', ''),
            ('dmm_blueoff', 'BlueLedOff', 'blue', ''),
            ('dmm_blueon', 'BlueLedOn', 'blue', ''),
            ('dmm_blueflash', 'BlueLedFlash', 'blue', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('trsrfm_btmac', 'BtMac', 'btmac', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ('arm_fltcode', 'ARM-FltCode', 'arm_fltcode', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ))
