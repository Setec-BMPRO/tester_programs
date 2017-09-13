#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Initial Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitBoolean, LimitRegExp
    )
import share
from . import console

class Initial(share.TestSequence):

    """BLE2CAN Initial Test Program."""

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
        LimitLow('TestPinCover', 0.5),
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
        """Test the operation of BLE2CAN."""
        ble2can = dev['ble2can']
        ble2can.open()
        dev['rla_reset'].pulse(0.1)
        ble2can.action(None, delay=5.0, expected=2)  # Flush banner
        ble2can['HW_VER'] = self.hw_ver
        ble2can['SER_ID'] = self.sernum
        ble2can['NVDEFAULT'] = True
        ble2can['NVWRITE'] = True
        mes['arm_swver']()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(self.vbatt, delay=15.0)
        btmac = mes['ble2can_btmac']().reading1
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
                ('dcs_cover', tester.DCSource, 'DCS5'),
                ('rla_reset', tester.Relay, 'RLA5'),
                ('rla_wdog', tester.Relay, 'RLA6'),
                ('rla_pin', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        self['ble2can_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['ble2can_ser'].port = share.port(self.fixture, 'ARM')
        # Console driver
        self['ble2can'] = console.Console(self['ble2can_ser'])
        # Serial connection to the BLE module
        self['ble_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        self['ble_ser'].port = share.port(self.fixture, 'BLE')
        self['ble'] = share.BleRadio(self['ble_ser'])
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
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        ble2can = self.devices['ble2can']
        self['btmac'] = console.Sensor(
            ble2can, 'BT_MAC', rdgtype=sensor.ReadingString)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('ble2can_initial', 'msgSnEntry'),
            caption=tester.translate('ble2can_initial', 'capSnEntry'))
        self['arm_swver'] = console.Sensor(
            ble2can, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('ble2can_btmac', 'BtMac', 'btmac', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ))
