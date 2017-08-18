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

    limits = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitDelta('3V3', 3.3, 0.25),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
        LimitBoolean('Notify', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limits, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Program', self._step_program, not self.fifo),
            TestStep('Bluetooth', self._step_bluetooth),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        dev['dcs_vin'].output(12.0, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the SAM device."""
        dev['program_sam'].program()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=15.0)
        btmac = mes['bc2_btmac']().reading1
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


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    # Test fixture item number
    fixture = '030451'

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_shunt', tester.DCSource, 'DCS3'),
                ('rla_prog', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # SAM device programmer
        self['program_sam'] = share.ProgramSAMB11(relay=self['rla_prog'])
        # Serial connection to the console
        self['bc2_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['bc2_ser'].port = share.port(self.fixture, 'ARM')
        # Console driver
        self['bc2'] = console.Console(self['bc2_ser'], verbose=False)
        # Serial connection to the BLE module
        self['ble_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        self['ble_ser'].port = share.port(self.fixture, 'BLE')
        self['ble'] = share.BleRadio(self['ble_ser'])
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(9.0, output=True, delay=5)

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vcom', 'dcs_vin', 'dcs_shunt'):
            self[dev].output(0.0, False)
        for rla in ('rla_prog', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        bc2 = self.devices['bc2']
        for name, cmdkey in (
                ('btmac', 'BT_MAC'),
            ):
            self[name] = console.Sensor(
                bc2, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('bc2_btmac', 'BtMac', 'btmac', ''),
            ))
