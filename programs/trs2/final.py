#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Final Program."""

import tester
from tester import TestStep, LimitLow, LimitDelta, LimitBoolean, LimitRegExp
import share
from . import console


class Final(share.TestSequence):

    """TRS2 Final Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        LimitDelta('Vin', 12.0, 0.5),
        LimitLow('TestPinCover', 0.5),
        LimitRegExp('BtMac', r'^[0-9A-F]{12}$'),
        LimitBoolean('DetectBT', True),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        mes['dmm_tstpincov'](timeout=5)
        dev['rla_pin'].set_on()
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(('dmm_vin', ), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(self.vbatt, delay=15.0)
        btmac = mes['trs2_btmac']().reading1
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
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_pin', tester.Relay, 'RLA6'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        self['trs2_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['trs2_ser'].port = share.port(self.fixture, 'ARM')
        # Console driver
        self['trs2'] = console.Console(self['trs2_ser'])
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


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['mirbt'] = sensor.Mirror()
        # Console sensors
        trs2 = self.devices['trs2']
        for name, cmdkey in (
                ('btmac', 'BT_MAC'),
            ):
            self[name] = console.Sensor(
                trs2, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('trs2_btmac', 'BtMac', 'btmac', ''),
            ))
