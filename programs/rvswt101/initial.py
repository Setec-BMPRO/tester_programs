#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Initial Test Program."""

import enum
import pathlib

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):

    """RVSWT101 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter, uut)
        Devices.sw_image = self.cfg['software']
        super().open(self.cfg['limits_ini'], Devices, Sensors, Measurements)
        # Force code the RVSWT101 switch code
        self.devices['progNORDIC'].rvswt101_forced_switch_code = (
            self.cfg['forced_code']
            )
        # Adjust for different console behaviour
        self.devices['rvswt101'].banner_lines = self.cfg['banner_lines']
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('ProgramTest', self._step_program_test),
            )
        # This is a multi-unit parallel program so we can't stop on errors.
        self.stop_on_failrdg = False
        # This is a multi-unit parallel program so we can't raise exceptions.
        tester.Tester.measurement_failure_exception = False

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        dev['dcs_vin'].output(3.3, output=True)
        mes['dmm_vin'].sensor.position = tuple(range(1, self.per_panel + 1))
        mes['dmm_vin'](timeout=5)

    @share.teststep
    def _step_program_test(self, dev, mes):
        """Program and test the board.

        Program the bluetooth device.
        Get the MAC address.
        Test the Bluetooth interface.

        """
        pgm = dev['progNORDIC']
        # Open console serial connection
        dev['rvswt101'].open()
        for pos in range(self.per_panel):
            mypos = pos + 1
            if tester.Measurement.position_enabled(mypos):
                # Set sensor positions
                for sen in (
                        pgm, mes['ble_mac'].sensor, mes['scan_mac'].sensor
                        ):
                    sen.position = mypos
                dev['fixture'].connect(mypos)
                pgm.program()
                if not tester.Measurement.position_enabled(mypos):
                    continue
                # Get the MAC address from the console.
                dev['dcs_vin'].output(0.0, delay=0.5)
                dev['rvswt101'].port.flushInput()
                dev['dcs_vin'].output(3.3, delay=0.1)
                self.mac = dev['rvswt101'].get_mac()
                mes['ble_mac'].sensor.store(self.mac)
                mes['ble_mac']()
                if not tester.Measurement.position_enabled(mypos):
                    continue
                # Save SerialNumber & MAC on a remote server.
                dev['serialtomac'].blemac_set(self.uuts[pos].sernum, self.mac)
                # Press Button2 to broadcast on bluetooth
                dev['fixture'].press(mypos)
                reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
                dev['fixture'].release()
                mes['scan_mac'].sensor.store(reply is not None)
                mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_usb', tester.DCSource, 'DCS4'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_switch', tester.DCSource, 'DCS3'),
                ('rla_pos1', tester.Relay, 'RLA1'),
                ('rla_pos2', tester.Relay, 'RLA2'),
                ('rla_pos3', tester.Relay, 'RLA3'),
                ('rla_pos4', tester.Relay, 'RLA4'),
                ('rla_pos5', tester.Relay, 'RLA5'),
                ('rla_pos6', tester.Relay, 'RLA6'),
                ('rla_pos7', tester.Relay, 'RLA7'),
                ('rla_pos8', tester.Relay, 'RLA8'),
                ('rla_pos9', tester.Relay, 'RLA9'),
                ('rla_pos10', tester.Relay, 'RLA10'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Fixture USB hub power
        self['dcs_usb'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_usb'].output(0.0, output=False))
        # Fixture helper device
        self['fixture'] = Fixture(
            self['dcs_switch'],
            [
                'Dummy entry to give 1-based relay number indexing',
                self['rla_pos1'], self['rla_pos2'], self['rla_pos3'],
                self['rla_pos4'], self['rla_pos5'], self['rla_pos6'],
                self['rla_pos7'], self['rla_pos8'], self['rla_pos9'],
                self['rla_pos10'],
            ]
            )
        # Nordic NRF52 device programmer
        self['progNORDIC'] = share.programmer.NRF52(
            pathlib.Path(__file__).parent / self.sw_image)
        # Serial connection to the console
        rvswt101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bl652_port = share.config.Fixture.port('032869', 'NORDIC')
        rvswt101_ser.port = bl652_port
        # RVSWT101 Console driver
        self['rvswt101'] = console.Console(rvswt101_ser)
        self['rvswt101'].measurement_fail_on_error = False
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()

    def reset(self):
        """Reset instruments."""
        self['rvswt101'].close()
        self['fixture'].reset()
        self['dcs_vin'].output(0.0, False)


class FixtureError(Exception):

    """Fixture operating sequence error."""


class FixtureState(enum.IntEnum):

    """State definitions for the Fixture class."""

    idle = 0
    program = 1
    button = 2


class Fixture():

    """Helper class for fixture circuit control.

    DC Source 'dcs' drives a relay that directs relay coil power to:
        - Button press relays (when DCS is off)
        - Programmer/Console connection relays (when DCS is 12V)
    The list of relays 'relays' controls each of the fixture positions.
    Depending upon 'dcs', it will either press that positions button, or
    connect the programmer & console to that position.

    This class deals with the settings and sequencing.

    """

    # DC Source set voltages for each mode
    dcs_program = 12.0
    dcs_button = 0.0
    # Delay after setting DC Source
    dcs_delay = 0.1

    def __init__(self, dcs, relays):
        """Create instance.

        @param dcs DC Source instance controlling Program / Button mode
        @param relays List of position connection relays, with a leading
                        [0] dummy entry

        """
        self._dcs = dcs
        self._relays = relays
        # _position is 1-based:
        #   0 if nothing connected,
        #   (1-N) for a connected position
        self._position = 0
        self.state = None
        self.reset()

    def reset(self):
        """Reset operating state."""
        self._disconnect()
        self._dcs.output(0.0, output=False)
        self.state = FixtureState.idle

    def _connect(self, position):
        """Connect a position.

        @param position Position number (1-N)

        """
        if self._position:
            raise FixtureError('Concurrent connections are not allowed')
        self._relays[position].set_on()
        self._relays[position].opc()
        self._position = position

    def _disconnect(self):
        """Disconnect any connected position."""
        if self._position:
            self._relays[self._position].set_off()
            self._relays[self._position].opc()
            self._position = 0

    def connect(self, position):
        """Connect a position for programming.

        @param position Position number (1-N)

        """
        self._disconnect()
        if self.state != FixtureState.program: # Swap to PROGRAM mode
            self._dcs.output(
                self.dcs_program, output=True, delay=self.dcs_delay)
            self.state = FixtureState.program
        self._connect(position)

    def press(self, position):
        """Press a button.

        @param position Position number (1-N)

        """
        if self.state != FixtureState.button:  # Swap to BUTTON mode
            self._disconnect()
            self._dcs.output(
                self.dcs_button, output=True, delay=self.dcs_delay)
            self.state = FixtureState.button
        self._connect(position)

    def release(self):
        """Release a button."""
        if self.state != FixtureState.button:
            raise FixtureError('Release called in program mode')
        self._disconnect()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mirmac'] = sensor.MirrorReadingString()
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.01)
        # Console sensors
        rvswt101 = self.devices['rvswt101']
        for device, name, cmdkey in (
                (rvswt101, 'SwVer', 'SW_VER'),
            ):
            self[name] = sensor.KeyedReadingString(device, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from console'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ))
