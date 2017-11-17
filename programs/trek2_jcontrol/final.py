#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2/JControl Final Test Program."""

import tester
from tester import TestStep, LimitInteger, LimitRegExp
import share
from . import console
from . import config


class Final(share.TestSequence):

    """Trek2/JControl Final Test Program."""

    # Common limits
    _common = (
        LimitInteger('ARM-level1', 1),
        LimitInteger('ARM-level2', 2),
        LimitInteger('ARM-level3', 3),
        LimitInteger('ARM-level4', 4),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    limitdata = {
        'TK2': {
            'BinVer': config.SW_VERSION_TK2,
            'Limits': _common + (
                LimitRegExp('SwVer', '^{0}$'.format(
                    config.SW_VERSION_TK2.replace('.', r'\.'))),
                ),
            },
        'JC': {
            'BinVer': config.SW_VERSION_JC,
            'Limits': _common + (
                LimitRegExp('SwVer', '^{0}$'.format(
                    config.SW_VERSION_JC.replace('.', r'\.'))),
                ),
            },
        }

    def open(self):
        """Prepare for testing."""
        self.config = self.limitdata[self.parameter]
        super().open(
            self.config['Limits'], Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('TunnelOpen', self._step_tunnel_open),
            TestStep('Display', self._step_display),
            TestStep('Tanks', self._step_test_tanks),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev['dcs_Vin'].output(12.0, output=True, delay=9) # Wait for CAN bind

    @share.teststep
    def _step_tunnel_open(self, dev, mes):
        """Open console tunnel."""
        dev['armtunnel'].open()
        dev['armtunnel'].testmode(True)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display tests."""
        self.measure(('SwVer', 'ui_YesNoSeg', 'ui_YesNoBklight', ))
        dev['armtunnel'].testmode(False)

    @share.teststep
    def _step_test_tanks(self, dev, mes):
        """Test all tanks one level at a time."""
        dev['armtunnel']['CONFIG'] = 0x7E00      # Enable all 4 tanks
        dev['armtunnel']['TANK_SPEED'] = 0.1     # Change update interval
        # No sensors - Tanks empty!
        tester.MeasureGroup(mes['arm_level1'], timeout=12)
        # 1 sensor
        dev['rla_s1'].set_on()
        tester.MeasureGroup(mes['arm_level2'], timeout=12)
        # 2 sensors
        dev['rla_s2'].set_on()
        tester.MeasureGroup(mes['arm_level3'], timeout=12)
        # 3 sensors
        dev['rla_s3'].set_on()
        tester.MeasureGroup(mes['arm_level4'], timeout=12)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                # Power unit under test.
                ('dcs_Vin', tester.DCSource, 'DCS3'),
                # As the water level rises the "switches" close.
                # The order of switch closure does not matter, just the number
                # closed. The lowest bar always flashes.
                # Closing these relays makes the other bars come on.
                ('rla_s1', tester.Relay, 'RLA3'),
                ('rla_s2', tester.Relay, 'RLA4'),
                ('rla_s3', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        tunnel = share.can.Tunnel(
            self.physical_devices['CAN'], tester.CAN.DeviceID.trek2)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['armtunnel'].close()
        self['dcs_Vin'].output(0.0, output=False)
        for rla in ('rla_s1', 'rla_s2', 'rla_s3'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['oYesNoSeg'] = sensor.YesNo(
            message=tester.translate('trek2_jcontrol_final', 'AreSegmentsOn?'),
            caption=tester.translate('trek2_jcontrol_final', 'capSegments'))
        self['oYesNoBklight'] = sensor.YesNo(
            message=tester.translate('trek2_jcontrol_final', 'IsBacklightOk?'),
            caption=tester.translate('trek2_jcontrol_final', 'capBacklight'))
        self['otanks'] = (
            share.console.Sensor(armtunnel, 'TANK1'),
            share.console.Sensor(armtunnel, 'TANK2'),
            share.console.Sensor(armtunnel, 'TANK3'),
            share.console.Sensor(armtunnel, 'TANK4'),
            )
        # Console sensors
        self['SwVer'] = share.console.Sensor(
            armtunnel, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_YesNoSeg', 'Notify', 'oYesNoSeg', ''),
            ('ui_YesNoBklight', 'Notify', 'oYesNoBklight', ''),
            ('SwVer', 'SwVer', 'SwVer', ''),
            ))
        self['arm_level1'] = []
        self['arm_level2'] = []
        self['arm_level3'] = []
        self['arm_level4'] = []
        meas = tester.Measurement
        for sens in self.sensors['otanks']:
            self['arm_level1'].append(
                meas(self.limits['ARM-level1'], sens))
            self['arm_level2'].append(
                meas(self.limits['ARM-level2'], sens))
            self['arm_level3'].append(
                meas(self.limits['ARM-level3'], sens))
            self['arm_level4'].append(
                meas(self.limits['ARM-level4'], sens))
