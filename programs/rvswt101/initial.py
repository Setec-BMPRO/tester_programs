#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Initial Test Program."""

import os
import inspect
import serial
import tester
from tester import (
    LimitDelta,
    LimitRegExp, LimitBoolean
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RVSWT101 Initial Test Program."""

    limitdata = (
        LimitDelta('Vin', 3.3, 0.3),
        LimitBoolean('ScanMac', True, doc='MAC address detected'),
        LimitRegExp('BleMac', '^[0-9a-f]{12}$', doc='Valid MAC address'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.sw_image = config.SW_IMAGE.format(self.parameter)
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
            tester.TestStep('GetMac', self._step_get_mac),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        self.sernum = 'A0000000000'
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        self.dcsource(
            (('dcs_vcom', 9.0), ('dcs_vin', 3.3), ('dcs_switch', 12.0)),
            output=True, delay=5)
        mes['dmm_vin'](timeout=5)
        dev['rla_pos1'].set_on()

    @share.teststep
    def _step_get_mac(self, dev, mes):
        """Get the MAC address from the console."""
        dev['rla_disconct'].set_on(delay=0.1)
        rvswt101 = dev['rvswt101']
        rvswt101.open()
        # Reset or cycle power to get the banner from the Nordic
        self.mac = rvswt101.get_mac(dev['rla_reset'])
        mes['ble_mac'].sensor.store(self.mac)
        mes['ble_mac']()
        # Save SerialNumber & MAC on a remote server
        dev['serialtomac'].blemac_set(self.sernum, self.mac)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        # Press Button2 to broadcast on bluetooth
        dev['rla_pos1'].set_off(delay=0.1)
        dev['dcs_switch'].output(0, delay=0.1)
        dev['rla_pos1'].pulse(0.1)
        reply = dev['pi_bt'].scan_advert_blemac(self.mac)
        mes['scan_mac'].sensor.store(reply)
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
                ('rla_reset', tester.Relay, 'RLA21'),
                ('rla_disconct', tester.Relay, 'RLA22'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # NRF52 device programmer
        self['progNRF'] = share.programmer.Nordic(
            os.path.join(folder, self.sw_image),
            folder)
        # Serial connection to the BL652 console
        rvswt101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bl652_port = share.fixture.port('032869', 'BL652')
        rvswt101_ser.port = bl652_port
        # RVSWT101 Console driver
        self['rvswt101'] = console.Console(rvswt101_ser)
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()
        # Connection to Serial To MAC server
        self['serialtomac'] = config.SerialToMAC()

    def reset(self):
        """Reset instruments."""
        self['rvswt101'].close()
        for dcs in ('dcs_vcom', 'dcs_vin', 'dcs_switch'):
            self[dcs].output(0.0, False)
        for rla in ('rla_pos1', 'rla_reset', 'rla_disconct'):
            self[rla].set_off()


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
