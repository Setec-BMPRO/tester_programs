#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Initial Test Program."""

import inspect
import os

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):

    """RVSWT101 Initial Test Program."""

    limitdata = (
        tester.LimitDelta('Vin', 3.3, 0.3),
        tester.LimitBoolean('ScanMac', True,
            doc='MAC address detected'),
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.sw_image = config.SW_IMAGE.format(self.parameter)
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('ProgramTest', self._step_program_test),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vin'].output(3.3, output=True)
        mes['dmm_vin'](timeout=5)

    @share.teststep
    def _step_program_test(self, dev, mes):
        """Program and test the board.

        Program the bluetooth device.
        Get the MAC address.
        Test the Bluetooth interface.

        """
        pgm = dev['progNORDIC']
        for pos in range(self.per_panel):
            if tester.Measurement.position_enabled(pos + 1):
                with tester.PathName('Brd{0}'.format(pos + 1)):
                    dev['fixture'].connect(pos)
                    pgm.position = pos + 1
                    pgm.program()
                    # Get the MAC address from the console.
                    dev['dcs_vin'].output(0.0, delay=0.5)
                    dev['rvswt101'].port.flushInput()
                    dev['dcs_vin'].output(3.3, delay=0.1)
                    self.mac = dev['rvswt101'].get_mac()
                    mes['ble_mac'].sensor.store(self.mac)
                    mes['ble_mac']()
                    # Save SerialNumber & MAC on a remote server.
                    dev['serialtomac'].blemac_set(self.sernum, self.mac)
                    # Press Button2 to broadcast on bluetooth
                    dev['fixture'].press(pos)
                    reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
                    dev['fixture'].release(pos)
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
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_switch', tester.DCSource, 'DCS3'),
                ('rla_pos1', tester.Relay, 'RLA1'),
                ('rla_pos2', tester.Relay, 'RLA2'),
                ('rla_pos3', tester.Relay, 'RLA3'),
                ('rla_pos4', tester.Relay, 'RLA4'),
                ('rla_pos5', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Fixture helper device
        self['fixture'] = Fixture(
            self['dcs_switch'],
            [self['rla_pos1'], self['rla_pos2'], self['rla_pos3'],
            self['rla_pos4'], self['rla_pos5']]
            )
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # Nordic NRF52 device programmer
        self['progNORDIC'] = share.programmer.Nordic(
            os.path.join(folder, self.sw_image),
            folder)
        # Serial connection to the console
        rvswt101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bl652_port = share.fixture.port('032869', 'NORDIC')
        rvswt101_ser.port = bl652_port
        # RVSWT101 Console driver
        self['rvswt101'] = console.Console(rvswt101_ser)
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Connection to Serial To MAC server
        self['serialtomac'] = config.SerialToMAC()
        # Fixture USB hub power
        self['dcs_vcom'].output(9.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))
        # Open console serial connection
        self['rvswt101'].open()
        self.add_closer(lambda: self['rvswt101'].close())

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vin', 'dcs_switch'):
            self[dcs].output(0.0, False)
        for rla in (
            'rla_pos1', 'rla_pos2', 'rla_pos3', 'rla_pos4', 'rla_pos5'):
            self[rla].set_off()


class Fixture():

    """Helper class for fixture circuit control.

    DC Source 'mode_dcs' drives a relay that directs relay coil power to:
        - Button press relays (when DCS is off)
        - Programmer/Console connection relays (when DCS is 12V)
    The list of relays 'relays' controls each of the fixture positions.
    Depending upon 'mode_dcs', it will either press that positions button, or
    connect the programmer & console to that position.

    This class deals with the settings and sequencing.

    """

    def __init__(self, mode_dcs, relays):
        """Create instance.

        @param mode_dcs DC Source instance controlling Program / Button mode
        @param relays List of position connection relays

        """
        self.mode_dcs = mode_dcs
        self.relays = relays
        self.is_button_mode = None
        self.button_mode()

    def program_mode(self):
        """Set Program/Console mode."""
        if self.is_button_mode:
            for rla in self.relays:
                rla.set_off()
            self.mode_dcs.output(12, output=True, delay=0.1)
            self.is_button_mode = False

    def button_mode(self):
        """Set Button mode."""
        if not self.is_button_mode:
            for rla in self.relays:
                rla.set_off()
            self.mode_dcs.output(0, output=True, delay=0.1)
            self.is_button_mode = True

    def connect(self, position):
        """Connect a position for programming.

        @param position Position number

        """
        self.program_mode()
        self.relays[position].set_on()

    def disconnect(self, position):
        """Disconnect a position for programming.

        @param position Position number

        """
        self.program_mode()
        self.relays[position].set_off()

    def press(self, position):
        """Press a button.

        @param position Position number

        """
        self.button_mode()
        self.relays[position].set_on()

    def release(self, position):
        """Release a button.

        @param position Position number

        """
        self.button_mode()
        self.relays[position].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mirmac'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['mirscan'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.01)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvswt101_initial', 'msgSnEntry'),
            caption=tester.translate('rvswt101_initial', 'capSnEntry'))
        # Console sensors
        rvswt101 = self.devices['rvswt101']
        for device, name, cmdkey in (
                (rvswt101, 'SwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                device, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from console'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ))
