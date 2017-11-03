#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import inspect
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitDelta, LimitPercent, LimitInteger
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """Trek2 Initial Test Program."""

    # Input voltage to power the unit
    vin_set = 12.75
    # Test limits
    limitdata = (
        LimitDelta('Vin', vin_set - 0.75, 0.5),
        LimitPercent('3V3', 3.3, 3.0),
        LimitLow('BkLghtOff', 0.5),
        LimitDelta('BkLghtOn', 4.0, 0.55),      # 40mA = 4V with 100R (1%)
        # CAN Bus is operational if status bit 28 is set
        LimitInteger('CAN_BIND', 1 << 28),
        LimitRegExp('SwVer', '^{0}$'.format(
            config.SW_VERSION.replace('.', r'\.'))),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self.devices['programmer'].program),
            TestStep('TestArm', self._step_test_arm),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_SnEntry')
        dev['dcs_Vin'].output(self.vin_set, output=True)
        self.measure(('dmm_Vin', 'dmm_3V3'), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        trek2 = dev['trek2']
        trek2.open()
        trek2.brand(config.HW_VERSION, self.sernum, dev['rla_reset'])
        mes['SwVer']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['can_bind'](timeout=10)
        trek2tunnel = dev['trek2tunnel']
        trek2tunnel.open()
        mes['TunnelSwVer']()
        trek2tunnel.close()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_Vin', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            share.fixture.port('027420', 'ARM'),
            os.path.join(
                folder, 'Trek2_{0}.bin'.format(config.SW_VERSION)),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Direct Console driver
        trek2_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        trek2_ser.port = share.fixture.port('027420', 'ARM')
        self['trek2'] = console.DirectConsole(trek2_ser)
        # Tunneled Console driver
        tunnel = share.console.CanTunnel(
            self.physical_devices['CAN'], share.CanID.trek2)
        self['trek2tunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['trek2'].close()
        self['trek2tunnel'].close()
        self['dcs_Vin'].output(0.0, output=False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        trek2 = self.devices['trek2']
        trek2tunnel = self.devices['trek2tunnel']
        sensor = tester.sensor
        self['oMirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['oBkLght'] = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('trek2_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_initial', 'capSnEntry'),
            timeout=300)
        # Console sensors
        self['oCANBIND'] = console.Sensor(trek2, 'CAN_BIND')
        self['SwVer'] = console.Sensor(
            trek2, 'SW_VER', rdgtype=sensor.ReadingString)
        self['TunnelSwVer'] = console.Sensor(
            trek2tunnel, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_Vin', 'Vin', 'oVin', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_BkLghtOff', 'BkLghtOff', 'oBkLght', ''),
            ('dmm_BkLghtOn', 'BkLghtOn', 'oBkLght', ''),
            ('ui_SnEntry', 'SerNum', 'oSnEntry', ''),
            ('can_bind', 'CAN_BIND', 'oCANBIND', ''),
            ('SwVer', 'SwVer', 'SwVer', ''),
            ('TunnelSwVer', 'SwVer', 'TunnelSwVer', ''),
            ))
