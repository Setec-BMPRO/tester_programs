#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2/JControl Initial Test Program."""

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

    """Trek2/JControl Initial Test Program."""

    # Input voltage to power the unit
    vin_set = 12.75
    # Common limits
    _common = (
        LimitDelta('Vin', vin_set - 0.75, 0.5),
        LimitPercent('3V3', 3.3, 3.0),
        LimitLow('BkLghtOff', 0.5),
        LimitDelta('BkLghtOn', 4.0, 0.55),      # 40mA = 4V with 100R (1%)
        # CAN Bus is operational if status bit 28 is set
        LimitInteger('CAN_BIND', 1 << 28),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        'TK2': {
            'Config': config.Trek2,
            'Limits': _common + (
                LimitRegExp('SwVer', '^{0}$'.format(
                    config.Trek2.sw_version.replace('.', r'\.'))),
                ),
            },
        'JC': {
            'Config': config.JControl,
            'Limits': _common + (
                LimitRegExp('SwVer', '^{0}$'.format(
                    config.JControl.sw_version.replace('.', r'\.'))),
                ),
            },
        }

    def open(self):
        """Create the test program as a linear sequence."""
        self.config = self.config_data[self.parameter]['Config']
        Devices.prdt = self.config.product_name
        Devices.sw_ver = self.config.sw_version
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
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
        arm = dev['arm']
        arm.open()
        arm.brand(self.config.hw_version, self.sernum, dev['rla_reset'])
        mes['SwVer']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['can_bind'](timeout=10)
        armtunnel = dev['armtunnel']
        armtunnel.open()
        mes['TunnelSwVer']()
        armtunnel.close()


class Devices(share.Devices):

    """Devices."""

    sw_ver = None
    prdt = None

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
        arm_port = share.fixture.port('027420', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            arm_port,
            os.path.join(
                folder, '{0}_{1}.bin'.format(self.prdt, self.sw_ver)),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Direct Console driver
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        self['arm'] = console.DirectConsole(arm_ser)
        # Tunneled Console driver
        tunnel = share.can.Tunnel(
            self.physical_devices['CAN'], tester.CAN.DeviceID.trek2)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['armtunnel'].close()
        self['dcs_Vin'].output(0.0, output=False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        arm = self.devices['arm']
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['oMirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['oBkLght'] = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('trek2_jcontrol_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_jcontrol_initial', 'capSnEntry'),
            timeout=300)
        # Console sensors
        self['oCANBIND'] = share.console.Sensor(arm, 'CAN_BIND')
        self['SwVer'] = share.console.Sensor(
            arm, 'SW_VER', rdgtype=sensor.ReadingString)
        self['TunnelSwVer'] = share.console.Sensor(
            armtunnel, 'SW_VER', rdgtype=sensor.ReadingString)


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
