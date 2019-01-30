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
        LimitRegExp('SwNrfVer', '',            # Adjusted during open()
            doc='Nordic Software version'),
        LimitBoolean('ScanSer', True, doc='Serial number detected'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 3V3dc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vin'].output(3.2, output=True)
        dev['dcs_vcom'].output(5.0, output=True, delay=5)
        mes['dmm_vin'](timeout=5)
        dev['rla_switch'].set_on(delay=0.1)
        dev['rla_pos1'].set_on()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        # Reset or cycle power to get the banner from the Nordic
        dev['dcs_vin'].output(0, output=True, delay=2)
        dev['dcs_vin'].output(3.3, output=True)

        dev['rla_pos1'].set_off(delay=0.1)
        dev['rla_switch'].set_off(delay=0.1)
        dev['rla_pos1'].pulse(duration=0.1)
        reply = dev['pi_bt'].scan_advert_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply)
        mes['scan_ser']()


class Devices(share.Devices):

    """Devices."""

    sw_nrf_version = None   # Nordic software version

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_pos1', tester.Relay, 'RLA1'),
                ('rla_switch', tester.Relay, 'RLA21'),
                ('rla_reset', tester.Relay, 'RLA22'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # NRF52 device programmer
        self['progNRF'] = share.programmer.Nordic(
            os.path.join(
                folder,
                'rvswt101_nrf_{0}.hex'.format(config.SW_IMAGE)),
            folder)
        # Serial connection to the BL652 console
        rvswt101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bl652_port = share.fixture.port('012345', 'BL652')
        rvswt101_ser.port = bl652_port
        # RVSWT101 Console driver
        self['rvswt101'] = console.Console(rvswt101_ser)
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()

    def reset(self):
        """Reset instruments."""
        self['rvswt101'].close()
        for dcs in ('dcs_vcom', 'dcs_vin'):
            self[dcs].output(0.0, False)
        for rla in ('rla_pos1', 'rla_switch', 'rla_reset'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
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
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ))
