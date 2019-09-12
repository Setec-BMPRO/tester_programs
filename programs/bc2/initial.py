#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd.
"""BC2 Initial Program."""

import serial

import tester
import share

from . import config, console


class Initial(share.TestSequence):

    """BC2 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter)
        self.limits = self.cfg.limits_initial()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('Calibrate', self._step_calibrate),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.cfg.vbatt, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test operation."""
        bc2 = dev['bc2']
        bc2.open()
        bc2.brand(self.cfg.hw_version, self.sernum)
        bc2.set_model(self.cfg.model)
        mes['arm_swver']()

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate battery voltage gain and 0mA shunt current.

        Vbatt is at 15V, console is open.

        """
        bc2 = dev['bc2']
        dmm_v = mes['dmm_vin'].stable(delta=0.001).reading1
        mes['arm_vbatt'].testlimit[0].adjust(nominal=dmm_v)
        bc2['BATT_V_CAL'] = dmm_v
        mes['detectCAL'].sensor.store(bc2['LAST_RESPONSE?'][1])
        self.measure(('detectCAL', 'arm_vbatt'))
        bc2['ZERO_I_CAL'] = 0
        mes['detectCAL'].sensor.store(bc2['LAST_RESPONSE?'][1])
        self.measure(
            ('detectCAL', 'arm_ioffset', 'arm_ibattzero', 'arm_vbattlsb'))
        bc2['NVWRITE'] = True

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        btmac = share.bluetooth.MAC(mes['arm_btmac']().reading1)
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
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_wdog', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        bc2_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        bc2_ser.port = share.config.Fixture.port('030451', 'ARM')
        # Console driver
        self['bc2'] = console.Console(bc2_ser)
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=5.0, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.config.Fixture.port('030451', 'BLE')
        self['ble'] = share.bluetooth.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['bc2'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdog', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X4'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U2 output'
        self['mirbt'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['mircal'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        # Console sensors
        bc2 = self.devices['bc2']
        for name, cmdkey in (
                ('arm_BtMAC', 'BT_MAC'),
                ('arm_SwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                bc2, cmdkey, rdgtype=sensor.ReadingString)
        for name, cmdkey in (
                ('arm_Ioffset', 'I_ADC_OFFSET'),
                ('arm_VbattLSB', 'BATT_V_LSB'),
                ('arm_Vbatt', 'BATT_V'),
                ('arm_Ibatt', 'BATT_I'),
            ):
            self[name] = share.console.Sensor(bc2, cmdkey)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_initial', 'msgSnEntry'),
            caption=tester.translate('bc2_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('detectBT', 'DetectBT', 'mirbt', 'Scanned MAC address'),
            ('arm_btmac', 'BtMac', 'arm_BtMAC', 'MAC address'),
            ('arm_swver', 'ARM-SwVer', 'arm_SwVer', 'Unit software version'),
            ('detectCAL', 'ARM-CalOk', 'mircal',
                'Response from a calibration command'),
            ('arm_ioffset', 'ARM-I_ADCOffset', 'arm_Ioffset',
                'Current ADC offset after cal'),
            ('arm_vbattlsb', 'ARM-VbattLSB', 'arm_VbattLSB',
                'Battery voltage ADC LSB voltage after cal'),
            ('arm_vbatt', 'ARM-Vbatt', 'arm_Vbatt',
                'Battery voltage after cal'),
            ('arm_ibattzero', 'ARM-IbattZero', 'arm_Ibatt',
                'Battery current after zero cal'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ))
