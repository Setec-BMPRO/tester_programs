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
        tester.LimitDelta('Vin', 3.3, 0.3),
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$', doc='Valid MAC address'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.sw_image = config.SW_IMAGE.format(self.parameter)
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
            tester.TestStep('GetMac', self._step_get_mac),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vin'].output(3.3, output=True)
        mes['dmm_vin'](timeout=5)

    @share.teststep
    def _step_get_mac(self, dev, mes):
        """Get the MAC address from the console."""
        # Open console serial connection
        dev['rvmn101b'].open()
        dev['rla_nrf_reset'].disable(delay=0.1)
        # Cycle power to get the banner from the Nordic
        dev['dcs_vin'].output(0.0, delay=0.5)
        dev['rvmn101b'].port.flushInput()
        dev['dcs_vin'].output(3.3, delay=0.1)
        self.mac = dev['rvmn101b'].get_mac()
        mes['ble_mac'].sensor.store(self.mac)
        mes['ble_mac']()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        # Press Button2 to broadcast on bluetooth
        reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
        mes['scan_mac'].sensor.store(reply)
        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_nrf_reset', tester.Relay, 'RLA22'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        rla = self['rla_nrf_reset']
        rla.disable = rla.set_off
        rla.enable = rla.set_on
        # Working folder
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # ARM device programmer
        self['progARM'] = share.programmer.ARM(
            share.fixture.port('032871', 'ARM'),
            os.path.join(folder, config.SW_IMAGE),
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # NRF52 device programmer
        self['progNRF'] = share.programmer.Nordic(
            os.path.join(folder, config.SW_IMAGE),
            folder)
        # Serial connection to the BL652 console
        nordic_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_ser.port = share.fixture.port('032871', 'BL652')
        # Console driver
        self['rvmn101b'] = console.Console(nordic_ser)
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Fixture USB hub power
        self['dcs_vcom'].output(9.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vin', ):
            self[dcs].output(0.0, False)
        for rla in ('rla_pos1', 'rla_reset', 'rla_boot'):
            self[rla].set_off()
        self['rla_nrf_reset'].disable()
        self['rvmn101b'].close()


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
            ('dmm_vin', 'Vin', 'vin', ''),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from console'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ))
