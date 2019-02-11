#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVMC101 Initial Test Program."""

import os
import inspect
import serial
import tester
from tester import (
    LimitDelta,
    LimitInteger
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RVMC101 Initial Test Program."""

    limitdata = (
        LimitDelta('Vin', 12.0, 0.5, doc='Input voltage present'),
        LimitDelta('3V3', 3.3, 0.1, doc='3V3 present'),
        LimitDelta('5V', 5.0, 0.2, doc='5V present'),
        LimitInteger('CAN_BIND', 1 << 28, doc='CAN bus bound'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.sw_image = config.SW_IMAGE.format(self.parameter)
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self.devices['programmer'].program),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        self.dcsource(
            (('dcs_vcom', 9.0), ('dcs_vin', 3.3), ('dcs_switch', 12.0)),
            output=True, delay=5)
        mes['dmm_vin'](timeout=5)
        dev['rla_pos1'].set_on()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['cn101_can_bind'](timeout=10)
        cn101tunnel = dev['cn101tunnel']
        cn101tunnel.open()
        mes['TunnelSwVer']()
        cn101tunnel.close()


class Devices(share.Devices):

    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS1'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
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
        bl652_port = share.fixture.port('012345', 'BL652')
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
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o5v'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['o3v3'] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvmc101_initial', 'msgSnEntry'),
            caption=tester.translate('rvmc101_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_5v', 'Vin', 'o5v', '5V rail voltage'),
            ('dmm_3v3', 'Vin', 'o3v3', '3V3 rail voltage'),
            ('ui_serialnum', 'SerNum', 'SnEntry', 'Unit serial number'),
            ))
