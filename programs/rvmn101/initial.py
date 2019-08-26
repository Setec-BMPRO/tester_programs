#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Initial Test Program."""

import inspect
import os

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):

    """RVMN101 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter)
        Devices.fixture = self.cfg.fixture
        Devices.arm_image = self.cfg.arm_image
        Devices.nordic_image = self.cfg.nordic_image
        self.limits = self.cfg.limits_initial()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNordic'].program),
            tester.TestStep('Initialise', self._step_initialise),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('CanBus', self._step_canbus),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None
#        for mes in self.measurements:
#            print(str(self.measurements[mes]) + '\n')

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vbatt'].output(self.cfg.vbatt_set, output=True)
        self.measure(('dmm_vbatt', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the unit."""
        rvmn101 = dev['rvmn101']
        rvmn101.flushInput()
        # Cycle power to restart the unit
        dev['dcs_vbatt'].output(0.0, delay=0.5)
        dev['dcs_vbatt'].output(self.cfg.vbatt_set, delay=1.0)
        rvmn101.brand(
            self.sernum, self.cfg.product_rev, self.cfg.hardware_rev)
        # Save SerialNumber & MAC on a remote server.
        dev['serialtomac'].blemac_set(self.sernum, rvmn101.get_mac())

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the outputs of the unit."""
        rvmn101 = dev['rvmn101']
        dev['dcs_vhbridge'].output(self.cfg.vbatt_set, output=True, delay=0.2)
        if self.parameter == 'A':
            rvmn101.hs_output(41, False)
        mes['dmm_hs_off'](timeout=5)
        # Turn ON, then OFF, each HS output in turn
        for idx in rvmn101.valid_outputs:
            with tester.PathName('HS{0}'.format(idx)):
                rvmn101.hs_output(idx, True)
                mes['dmm_hs_on'](timeout=5)
                rvmn101.hs_output(idx, False)
                mes['dmm_hs_off'](timeout=5)
        # Turn ON, then OFF, each LS output in turn
        for idx, dmm_channel in (
                (rvmn101.ls_0a5_out1, 'dmm_ls1'),
                (rvmn101.ls_0a5_out2, 'dmm_ls2'),
                ):
            rvmn101.ls_output(idx, True)
            mes[dmm_channel + '_on'](timeout=5)
            rvmn101.ls_output(idx, False)
            mes[dmm_channel + '_off'](timeout=5)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        candev = dev['can']
        candev.verbose = True
        candev.flush_can()
        try:
            candev.read_can()
            result = True
        except tester.devphysical.can.SerialToCanError:
            result = False
        candev.verbose = False
        mes['can_active'].sensor.store(result)
        mes['can_active']()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.mac = mes['ble_mac']().reading1
        reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
        mes['scan_mac'].sensor.store(reply is not None)
        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    fixture = None          # Fixture number
    arm_image = None        # ARM software image filename
    nordic_image = None     # Nordic software image filename

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS4'),
                ('dcs_vbatt', tester.DCSource, 'DCS2'),
                ('dcs_vhbridge', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Working folder
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # ARM device programmer
        self['progARM'] = share.programmer.ARM(
            share.fixture.port(self.fixture, 'ARM'),
            os.path.join(folder, self.arm_image),
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Nordic NRF52 device programmer
        self['progNordic'] = share.programmer.Nordic(
            os.path.join(folder, self.nordic_image),
            folder)
        # Serial connection to the console
        nordic_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_ser.port = share.fixture.port(self.fixture, 'NORDIC')
        # Console driver
        self['rvmn101'] = {
            'A': console.ConsoleA,
            'B': console.ConsoleB,
            }[self.parameter](nordic_ser)
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        # CAN interface
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self.add_closer(self.close_can)
        # Fixture USB hub power
        self['dcs_vcom'].output(9.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))
        # Open console serial connection
        self['rvmn101'].open()
        self.add_closer(self['rvmn101'].close)

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vbatt', 'dcs_vhbridge'):
            self[dcs].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()

    def close_can(self):
        """Restore CAN interface to default settings."""
        candev = self['can']
        candev.rvc_mode = False
        candev.verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['MirScan'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['MirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['VBatt'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['HSout'] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.1)
        self['LSout1'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.1)
        self['LSout2'] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvmn101_initial', 'msgSnEntry'),
            caption=tester.translate('rvmn101_initial', 'capSnEntry'))
        # Console sensors
        rvmn101 = self.devices['rvmn101']
        for name, cmdkey in (
                ('BleMac', 'MAC'),
                ('SwRev', 'SW-REV'),
            ):
            self[name] = share.console.Sensor(
                rvmn101, cmdkey, rdgtype=sensor.ReadingString)
        # Convert "xx:xx:xx:xx:xx:xx (random)" to "xxxxxxxxxxxx"
        self['BleMac'].on_read = (
            lambda value: value.replace(':', '').replace(' (random)', '')
            )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_3v3', '3V3', '3V3', 'Micro power ok'),
            ('dmm_vbatt', 'Vbatt', 'VBatt', 'Battery input ok'),
            ('dmm_hs_off', 'HSoff', 'HSout', 'All high-side drivers OFF'),
            ('dmm_hs_on', 'HSon', 'HSout', 'High-side driver ON'),
            ('dmm_ls1_off', 'LSoff', 'LSout1', 'Low-side driver1 OFF'),
            ('dmm_ls1_on', 'LSon', 'LSout1', 'Low-side driver1 ON'),
            ('dmm_ls2_off', 'LSoff', 'LSout2', 'Low-side driver2 OFF'),
            ('dmm_ls2_on', 'LSon', 'LSout2', 'Low-side driver2 ON'),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('can_active', 'CANok', 'MirCAN', 'CAN bus traffic seen'),
            ('ble_mac', 'BleMac', 'BleMac', 'MAC address from console'),
            ('scan_mac', 'ScanMac', 'MirScan',
                'MAC address seen over bluetooth'),
            ))
