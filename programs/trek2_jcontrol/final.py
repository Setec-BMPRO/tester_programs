#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""JControl/Trek2/Trek3 Final Test Program."""

import logging

import tester

import share
from . import config, console


class Final(share.TestSequence):

    """Trek2/JControl Final Test Program."""

    # Input voltage to power the unit
    vin_set = 12.0
    # Time to wait for CAN binding (sec)
    can_bind_time = 9
    # Common limits
    _common = (
        tester.LimitInteger('ARM-level1', 1),
        tester.LimitInteger('ARM-level2', 2),
        tester.LimitInteger('ARM-level3', 3),
        tester.LimitInteger('ARM-level4', 4),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        'JC': {
            'Config': config.JControl,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.JControl.sw_version.replace('.', r'\.'))),
                ),
            },
        'TK2': {
            'Config': config.Trek2,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.Trek2.sw_version.replace('.', r'\.'))),
                ),
            },
        'TK3': {
            'Config': config.Trek3,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.Trek3.sw_version.replace('.', r'\.'))),
                ),
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        self.config = self.config_data[self.parameter]['Config']
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TunnelOpen', self._step_tunnel_open),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('Tanks', self._step_test_tanks),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(
            self.vin_set, output=True, delay=self.can_bind_time)
        self.send_preconditions(self.physical_devices['CAN'][0])

    @share.teststep
    def _step_tunnel_open(self, dev, mes):
        """Open console tunnel."""
        unit = dev['armtunnel']
        unit.open()
        unit.testmode(True)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display tests."""
        unit = dev['armtunnel']
        self.measure(('sw_ver', 'ui_yesnoseg', 'ui_yesnobklght', ))
        # Set unit internal Serial Number to match the outside label
        unit.set_sernum(self.sernum)

    @share.teststep
    def _step_test_tanks(self, dev, mes):
        """Test all tanks one level at a time."""
        unit = dev['armtunnel']
        unit['CONFIG'] = 0x7E00         # Enable all 4 tanks
        unit['TANK_SPEED'] = 0.1        # Change update interval
        try:
            # No sensors - Tanks empty
            dev['rla_s1'].set_off(delay=1)
            tester.MeasureGroup(mes['arm_level1'], timeout=12)
            # 1 sensor
            dev['rla_s1'].set_on(delay=1)
            tester.MeasureGroup(mes['arm_level2'], timeout=12)
            # 2 sensors
            dev['rla_s2'].set_on(delay=1)
            tester.MeasureGroup(mes['arm_level3'], timeout=12)
            # 3 sensors
            dev['rla_s3'].set_on(delay=1)
            tester.MeasureGroup(mes['arm_level4'], timeout=12)
        except tester.MeasurementFailedError:
            #Measure the 16 tank sensor input voltages.
            logger = logging.getLogger(__name__)
            logger.debug('Reading 16 tank sensor inputs')
            results = []
            for tank in range(1, 5):
                for sens in range(1, 5):
                    name = 'tank{0}_s{1}'.format(tank, sens)
                    sens = self.sensors[name]
                    sens.configure()
                    value = sens.read()
                    results.append((name, value))
            logger.debug('Results => %s', results)
            raise
        unit.testmode(False)

    @staticmethod
    def send_preconditions(candev):
        """Send a Preconditions packet (for Trek2)."""
        header = tester.devphysical.can.SETECHeader()
        msg = header.message
        msg.device_id = share.can.SETECDeviceID.BP35.value
        msg.msg_type = tester.devphysical.can.SETECMessageType.ANNOUNCE.value
        msg.data_id = tester.devphysical.can.SETECDataID.PRECONDITIONS.value
        data = b'\x00\x00'      # Dummy data
        candev.send(tester.devphysical.can.CANPacket(header, data))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                # Power unit under test.
                ('dcs_vin', tester.DCSource, 'DCS1'),
                # As the water level rises the "switches" close.
                # The order of switch closure does not matter, just the number
                # closed. The lowest bar always flashes.
                # Closing these relays makes the other bars come on.
                ('rla_s1', tester.Relay, 'RLA3'),
                ('rla_s2', tester.Relay, 'RLA4'),
                ('rla_s3', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            share.can.SETECDeviceID.TREK2.value)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['armtunnel'].close()
        self['dcs_vin'].output(0.0, output=False)
        for rla in ('rla_s1', 'rla_s2', 'rla_s3'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['yesnoseg'] = sensor.YesNo(
            message=tester.translate('trek2_jcontrol_final', 'AreSegmentsOn?'),
            caption=tester.translate('trek2_jcontrol_final', 'capSegments'))
        self['yesnoseg'].doc = 'Operator input'
        self['yesnobklght'] = sensor.YesNo(
            message=tester.translate('trek2_jcontrol_final', 'IsBacklightOk?'),
            caption=tester.translate('trek2_jcontrol_final', 'capBacklight'))
        self['yesnobklght'].doc = 'Operator input'
        # 16 sensors: 4 Tanks, each with 4 Sensors
        for tank in range(1, 5):
            for sens in range(1, 5):
                name = 'tank{0}_s{1}'.format(tank, sens)
                key = 'TANK{0}_S{1}'.format(tank, sens)
                self[name] = sensor.KeyedReading(armtunnel, key)
        self['tank1-4'] = (
            sensor.KeyedReading(armtunnel, 'TANK1'),
            sensor.KeyedReading(armtunnel, 'TANK2'),
            sensor.KeyedReading(armtunnel, 'TANK3'),
            sensor.KeyedReading(armtunnel, 'TANK4'),
            )
        self['swver'] = sensor.KeyedReadingString(armtunnel, 'SW_VER')
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('j35_final', 'msgSnEntry'),
            caption=tester.translate('j35_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('ui_yesnoseg', 'Notify', 'yesnoseg', 'Segment display'),
            ('ui_yesnobklght', 'Notify', 'yesnobklght', 'Backlight'),
            ('sw_ver', 'SwVer', 'swver', 'Unit software version'),
            ))
        self['arm_level1'] = []
        self['arm_level2'] = []
        self['arm_level3'] = []
        self['arm_level4'] = []
        meas = tester.Measurement
        for sens in self.sensors['tank1-4']:
            self['arm_level1'].append(
                meas(self.limits['ARM-level1'], sens))
            self['arm_level2'].append(
                meas(self.limits['ARM-level2'], sens))
            self['arm_level3'].append(
                meas(self.limits['ARM-level3'], sens))
            self['arm_level4'].append(
                meas(self.limits['ARM-level4'], sens))
