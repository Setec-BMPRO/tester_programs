#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Initial Test Program."""

import tester
from tester import TestStep, LimitLow, LimitDelta,  LimitBetween, LimitPercent
import share

VIN_SET = 30.0      # Input voltage setting
VOUT = 15.5
VOUT_MIN = VOUT * (1.0 - ((2.0 + 1.5) / 100))   # Vout - 2% - 1.5%
IOUT_FL = 1.0       # Max output current
OCP_START = 0.9     # OCP measurement parameters
OCP_STOP = 1.5
OCP_STEP = 0.02
OCP_DELAY = 0.05


class Initial(share.TestSequence):

    """C15D-15 Initial Test Program."""

    limitdata = (
        LimitDelta('Vin', VIN_SET, 2.0),
        LimitBetween('Vcc', 11.0, 14.0),
        LimitPercent('VoutNL', VOUT, 2.0),
        LimitPercent('VoutFL', VOUT, (2.0 + 1.5, 2.0)),
        LimitBetween('VoutOCP', 12.5, VOUT_MIN),
        LimitLow('LedOff', 0.5),
        LimitBetween('LedOn', 7.0, 13.5),
        LimitLow('inOCP', VOUT_MIN),
        LimitBetween('OCP', 1.0, 1.4),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('OCP', self._step_ocp),
            TestStep('Charging', self._step_charging),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up."""
        dev['dcl'].output(0.0, output=True)
        dev['dcs_input'].output(VIN_SET, output=True)
        self.measure(
            ('dmm_vin', 'dmm_vcc', 'dmm_vout_nl', 'dmm_green_on',
             'dmm_yellow_off', ), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes['ramp_ocp']()
        dev['dcl'].output(0.0)

    @share.teststep
    def _step_charging(self, dev, mes):
        """Load into OCP for charging check."""
        dev['rla_load'].set_on()
        self.measure(
            ('dmm_vout_ocp', 'dmm_green_on', 'dmm_yellow_on', ),
            timeout=5)
        dev['rla_load'].set_off()
        mes['dmm_vout_nl'](timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_input', tester.DCSource, 'DCS1'),
                ('dcl', tester.DCLoad, 'DCL1'),
                ('rla_load', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['dcs_input'].output(0.0, False)
        self['dcl'].output(0.0, False)
        self['rla_load'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vcc'] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self['led_green'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self['led_yellow'] = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self['vout'] = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['vout'],
            detect_limit=(self.limits['inOCP'], ),
            start=OCP_START, stop=OCP_STOP, step=OCP_STEP, delay=OCP_DELAY)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_vcc', 'Vcc', 'vcc', ''),
            ('dmm_vout_nl', 'VoutNL', 'vout', ''),
            ('dmm_vout_fl', 'VoutFL', 'vout', ''),
            ('dmm_vout_ocp', 'VoutOCP', 'vout', ''),
            ('dmm_green_on', 'LedOn', 'led_green', ''),
            ('dmm_yellow_off', 'LedOff', 'led_yellow', ''),
            ('dmm_yellow_on', 'LedOn', 'led_yellow', ''),
            ('ramp_ocp', 'OCP', 'ocp', ''),
            ))
