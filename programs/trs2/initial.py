#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Initial Program."""

import os
import inspect
import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitDelta, LimitBoolean, LimitRegExp
    )
import share
from . import console

SAM_HEX = 'trs2_test.hex'

# Serial port for the programmer.
PROG_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM17'}[os.name]
# Serial port for the ARM. Used by ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM18'}[os.name]
# Serial port for the Bluetooth module.
BLE_PORT = {'posix': '/dev/ttyUSB2', 'nt': 'COM19'}[os.name]

VBATT = 12.0

LIMITS = (
    LimitDelta('Vin', 12.0, 0.5),
    LimitDelta('3V3', 3.3, 0.25),
    LimitLow('BrakeOff', 0.5),
    LimitDelta('BrakeOn', VBATT, (0.5, 0)),
    LimitLow('LightOff', 0.5),
    LimitDelta('LightOn', VBATT, (0.25, 0)),
    LimitLow('RemoteOff', 0.5),
    LimitDelta('RemoteOn', VBATT, (0.25, 0)),
    LimitHigh('RedLedOff', 3.0),
    LimitLow('RedLedOn', 0.1),
    LimitHigh('GreenLedOff', 3.0),
    LimitLow('GreenLedOn', 0.1),
    LimitHigh('BlueLedOff', 3.0),
    LimitLow('BlueLedOn', 0.1),
    LimitRegExp('BtMac', r'^[0-F]{12}$'),
    LimitBoolean('DetectBT', True),
    LimitBoolean('Notify', True),
    )


class Initial(share.TestSequence):

    """TRS2 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Program', self._step_program, not self.fifo),
            TestStep('Test', self._step_test),
            TestStep('Bluetooth', self._step_bluetooth),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        dev['rla_pin'].set_on()
        dev['dcs_vin'].output(VBATT, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the SAM device."""
        dev['program_sam'].program()

    @share.teststep
    def _step_test(self, dev, mes):
        """Test the operation of TRS2."""

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(VBATT, delay=15.0)
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

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_prog', tester.Relay, 'RLA2'),
                ('rla_pin', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # SAM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_sam'] = share.ProgramSAM(
            SAM_HEX, folder, 'SAM B11-MR210CA', self['rla_prog'])
        # Serial connection to the console
        self['trs2_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['trs2_ser'].port = ARM_PORT
        # Console driver
        self['trs2'] = console.Console(self['trs2_ser'], verbose=False)
        # Serial connection to the BLE module
        self['ble_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        self['ble_ser'].port = BLE_PORT
        self['ble'] = share.BleRadio(self['ble_ser'])
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(9.0, output=True, delay=5)

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vcom', 'dcs_vin',):
            self[dev].output(0.0, False)
        for rla in ('rla_prog', 'rla_pin', ):
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
        self['blue'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self['brake'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.01)
        self['light'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.01)
        self['remote'] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
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
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_brakeoff', 'BrakeOff', 'brake', ''),
            ('dmm_brakeon', 'BrakeOn', 'brake', ''),
            ('dmm_lightoff', 'LightOff', 'light', ''),
            ('dmm_lighton', 'LightOn', 'light', ''),
            ('dmm_remoteoff', 'RemoteOff', 'remote', ''),
            ('dmm_remoteon', 'RemoteOn', 'remote', ''),
            ('dmm_redoff', 'RedLedOff', 'red', ''),
            ('dmm_redon', 'RedLedOn', 'red', ''),
            ('dmm_greenoff', 'RedLedOff', 'green', ''),
            ('dmm_greenon', 'RedLedOn', 'green', ''),
            ('dmm_blueoff', 'RedLedOff', 'blue', ''),
            ('dmm_blueon', 'RedLedOn', 'blue', ''),
            ('detectBT', 'DetectBT', 'mirbt', ''),
            ('trs2_btmac', 'BtMac', 'btmac', ''),
            ))
