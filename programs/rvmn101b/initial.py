#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101B Initial Test Program."""

import os
import inspect
import serial
import tester
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RVMN101B Initial Test Program."""

    limitdata = (
        tester.LimitDelta('Vbatt', 12.0, 0.5),
        tester.LimitDelta('3V3', 3.3, 0.3),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )
    vbatt_set = 12.5

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNordic'].program),
            tester.TestStep('CanBus', self._step_canbus),
            tester.TestStep('GetMac', self._step_get_mac),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vbatt'].output(self.vbatt_set, output=True)
        self.measure(('dmm_vbatt', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        dev['dcs_vbatt'].output(0.0, delay=0.5)
#        dev['rvmn101b'].port.flushInput()
        dev['dcs_vbatt'].output(self.vbatt_set, delay=0.1)
        candev = dev['can']
        candev.verbose = True
        candev.flush_can()      # Flush all waiting packets
        try:
            candev.read_can()
            result = True
        except tester.devphysical.can.SerialToCanError:
            result = False
        mes['can_active'].sensor.store(result)
        mes['can_active']()

    @share.teststep
    def _step_get_mac(self, dev, mes):
        """Get the MAC address from the console."""
#        self.mac = dev['rvmn101b'].get_mac()
#        mes['ble_mac'].sensor.store(self.mac)
#        mes['ble_mac']()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
#        reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
#        mes['scan_mac'].sensor.store(reply)
#        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
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
            share.fixture.port('032871', 'ARM'),
            os.path.join(folder, config.ARM_IMAGE),
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Nordic NRF52 device programmer
        self['progNordic'] = share.programmer.Nordic(
            os.path.join(folder, config.NORDIC_IMAGE),
            folder)
        # Serial connection to the console
        nordic_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_ser.port = share.fixture.port('032871', 'NORDIC')
        # Console driver
        self['rvmn101b'] = console.Console(nordic_ser)
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # CAN interface
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self.add_closer(self.close_can)
        # Fixture USB hub power
        self['dcs_vcom'].output(9.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))
#        # Open console serial connection
#        self['rvmn101b'].open()
#        self.add_closer(lambda: self['rvnm101b'].close())

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vbatt', ):
            self[dcs].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()

    def close_can(self):
        """Restore CAN interface to default settings."""
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['MirMAC'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['MirScan'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['MirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['vbatt'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvmn101b_initial', 'msgSnEntry'),
            caption=tester.translate('rvmn101b_initial', 'capSnEntry'))
        # Console sensors
        rvmn101b = self.devices['rvmn101b']
        for device, name, cmdkey in (
                (rvmn101b, 'SwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                device, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_3v3', '3V3', '3v3', ''),
            ('dmm_vbatt', 'Vbatt', 'vbatt', ''),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('can_active', 'CANok', 'MirCAN', 'CAN bus traffic seen'),
            ('ble_mac', 'BleMac', 'MirMAC', 'Get MAC address from console'),
            ('scan_mac', 'ScanMac', 'MirScan',
                'Scan for MAC address over bluetooth'),
            ))
