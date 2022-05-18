#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""C15D-15 Initial Test Program."""

import tester

import share


class Initial(share.TestSequence):

    """C15D-15 Initial Test Program."""

    vin_set = 30.0      # Input voltage setting
    vout = 15.5
    vout_min = vout * (1.0 - ((2.0 + 1.5) / 100))   # Vout - 2% - 1.5%
    limitdata = (
        tester.LimitDelta('Vin', vin_set, 2.0),
        tester.LimitBetween('Vcc', 11.0, 14.0),
        tester.LimitPercent('VoutNL', vout, 2.0),
        tester.LimitPercent('VoutFL', vout, (2.0 + 1.5, 2.0)),
        tester.LimitBetween('VoutOCP', 12.5, vout_min),
        tester.LimitLow('LedOff', 0.5),
        tester.LimitBetween('LedOn', 7.0, 13.5),
        tester.LimitLow('inOCP', vout_min),
        tester.LimitBetween('OCP', 1.0, 1.4),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Charging', self._step_charging),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up."""
        dev['dcl'].output(0.0, output=True)
        dev['dcs_input'].output(self.vin_set, output=True)
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
        with dev['rla_load']:
            self.measure(
                ('dmm_vout_ocp', 'dmm_green_on', 'dmm_yellow_on', ),
                timeout=5)
        mes['dmm_vout_nl'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
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
            detect_limit=self.limits['inOCP'],
            ramp_range=sensor.RampRange(start=0.9, stop=1.5, step=0.02),
            delay=0.05)


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
