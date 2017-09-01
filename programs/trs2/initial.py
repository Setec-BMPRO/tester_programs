#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Initial Program."""

import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitDelta, LimitBoolean, LimitRegExp
    )
import share
from . import console

class Initial(share.TestSequence):

    """TRS2 Initial Test Program."""

    arm_version = '1.0.16281.446'
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_ver = (1, 0, 'A')
    # Injected Vbatt
    vbatt = 12.0
    #Manual override parameters
    force_on = 2
    force_off = 1
    normal = 0
    # Test limits
    limits = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('3V3', 3.3, 0.25),
        LimitLow('BrakeOff', 0.5),
        LimitDelta('BrakeOn', vbatt, (0.5, 0)),
        LimitLow('LightOff', 0.5),
        LimitDelta('LightOn', vbatt, (0.25, 0)),
        LimitLow('RemoteOff', 0.5),
        LimitDelta('RemoteOn', vbatt, (0.25, 0)),
        LimitHigh('RedLedOff', 3.1),
        LimitDelta('RedLedOn', 0.5, 0.05),
        LimitHigh('GreenLedOff', 3.1),
        LimitLow('GreenLedOn', 0.15),
        LimitHigh('BlueLedOff', 3.1),
        LimitDelta('BlueLedOn', 0.25, 0.05),
        LimitDelta('BlueLedFlash', 1.6, 0.2),
        LimitLow('TestPinCover', 0.5),
        LimitRegExp('SerNum', '^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
        LimitRegExp('ARM-SwVer',
            '^{}$'.format(arm_version.replace('.', r'\.'))),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
        LimitBoolean('Notify', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limits, LogicalDevices, Sensors, Measurements)
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
        mes['dmm_tstpincov'](timeout=5)
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes['ui_sernum'])
        dev['rla_pin'].set_on()
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(('dmm_vin', 'dmm_3v3', 'dmm_brakeoff'), timeout=5)
        dev['rla_pin'].set_off()
        mes['dmm_brakeon'](timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the operation of TRS2."""
        trs2 = dev['trs2']
        trs2.open()
        dev['rla_reset'].pulse(0.1)
        trs2.action(None, delay=5.0, expected=2)  # Flush banner
        trs2['FAULT_CODE']
        trs2['BATT_CHANGE']
        trs2['STATE']
        trs2['HW_VER'] = self.hw_ver
        trs2['SER_ID'] = self.sernum
        trs2['NVDEFAULT'] = True
        trs2['NVWRITE'] = True
        mes['arm_swver']()
        self.measure(
            ('dmm_redoff', 'dmm_greenoff', 'dmm_blueflash'), timeout=5)
        trs2.override(self.force_on)
        self.measure(
            ('dmm_lighton', 'dmm_remoteon', 'dmm_redon', 'dmm_greenon',
            'dmm_blueon'), timeout=5)
        trs2.override(self.force_off)
        self.measure(
            ('dmm_lightoff', 'dmm_remoteoff', 'dmm_redoff', 'dmm_greenoff',
            'dmm_blueoff'), timeout=5)
        trs2.override(self.normal)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        trs2 = dev['trs2']
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(self.vbatt, delay=15.0)
        btmac = mes['trs2_btmac']().reading1
        trs2['BLUETOOTH'] = self.force_on
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        if self.fifo:
            reply = True
        else:
            ble = dev['ble']
            ble.open()
            time.sleep(3)
            reply = ble.scan(btmac)
            ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        trs2['BLUETOOTH'] = self.normal
        mes['detectBT'].sensor.store(reply)
        mes['detectBT']()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    # Test fixture item number
    fixture = '030451'

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA5'),
                ('rla_wdg', tester.Relay, 'RLA6'),  #Normally closed
                ('rla_pin', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        self['trs2_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['trs2_ser'].port = share.port(self.fixture, 'ARM')
        # Console driver
        self['trs2'] = console.Console(self['trs2_ser'], verbose=False)
        # Serial connection to the BLE module
        self['ble_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        self['ble_ser'].port = share.port(self.fixture, 'BLE')
        self['ble'] = share.BleRadio(self['ble_ser'])
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vin', ):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdg', 'rla_pin'):
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
        self['blue'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01, nplc=10)
        self['brake'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.01)
        self['light'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.01)
        self['remote'] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        trs2 = self.devices['trs2']
        self['btmac'] = console.Sensor(
            trs2, 'BT_MAC', rdgtype=sensor.ReadingString)
        for name, cmdkey in (
                ('btmac', 'BT_MAC'),
            ):
            self[name] = console.Sensor(
                trs2, cmdkey, rdgtype=sensor.ReadingString)
        self['arm_swver'] = console.Sensor(
            trs2, 'SW_VER', rdgtype=sensor.ReadingString)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trs2_initial', 'msgSnEntry'),
            caption=tester.translate('trs2_initial', 'capSnEntry'))
        self['yesnoblue'] = sensor.YesNo(
            message=tester.translate('trs2_initial', 'IsBlueFlash?'),
            caption=tester.translate('trs2_initial', 'capBlueLed'))
        self['yesnooff'] = sensor.YesNo(
            message=tester.translate('trs2_initial', 'IsLedOff?'),
            caption=tester.translate('trs2_initial', 'capLeds'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_brakeoff', 'BrakeOff', 'brake', ''),
            ('dmm_brakeon', 'BrakeOn', 'brake', ''),
            ('dmm_lightoff', 'LightOff', 'light', ''),
            ('dmm_lighton', 'LightOn', 'light', ''),
            ('dmm_remoteoff', 'RemoteOff', 'remote', ''),
            ('dmm_remoteon', 'RemoteOn', 'remote', ''),
            ('dmm_redoff', 'RedLedOff', 'red', ''),
            ('dmm_redon', 'RedLedOn', 'red', ''),
            ('dmm_greenoff', 'GreenLedOff', 'green', ''),
            ('dmm_greenon', 'GreenLedOn', 'green', ''),
            ('dmm_blueoff', 'BlueLedOff', 'blue', ''),
            ('dmm_blueon', 'BlueLedOn', 'blue', ''),
            ('dmm_blueflash', 'BlueLedFlash', 'blue', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('trs2_btmac', 'BtMac', 'btmac', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('ui_yesnoblue', 'Notify', 'yesnoblue', ''),
            ('ui_yesnooff', 'Notify', 'yesnooff', ''),
            ))
