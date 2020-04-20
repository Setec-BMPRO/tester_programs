#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2014 SETEC Pty Ltd.
"""GSU360-1TA Final Test Program."""

import tester

import share


class Final(share.TestSequence):

    """GSU360-1TA Final Test Program."""

    limitdata = (
        tester.LimitBetween('24V', 23.40, 24.60),
        tester.LimitLow('24Vinocp', 23.4),
        tester.LimitBetween('24Vocp', 15.5, 20.0),
        tester.LimitLow('24Voff', 5.0),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Shutdown', self._step_shutdown),
            tester.TestStep('Restart', self._step_restart),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit at 240Vac."""
        dev['dcl_24V'].output(0.5, output=True)
        dev['acsource'].output(240.0, output=True, delay=0.5)
        self.measure(('dmm_24V', 'ui_YesNoGreen', ), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        dev['dcl_24V'].binary(0.0, 15.0, 4.0)
        mes['dmm_24V'](timeout=5)
        dev['acsource'].output(110.0)
        mes['dmm_24V'](timeout=5)
        dev['acsource'].output(240.0, output=True, delay=0.5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point (Load is already at 15.0A)."""
        mes['ramp_24Vocp']()

    @share.teststep
    def _step_shutdown(self, dev, mes):
        """Overload unit, measure."""
        dev['dcl_24V'].output(21.0)
        mes['dmm_24Voff'](timeout=5)

    @share.teststep
    def _step_restart(self, dev, mes):
        """Re-Start unit after Shutdown."""
        dev['dcl_24V'].output(0.0)
        mes['dmm_24V'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_24V', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_24V'].output(5.0, delay=20)   # Allow time to discharge
        self['dcl_24V'].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['o24V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['oYesNoGreen'] = sensor.YesNo(
            message=tester.translate('gsu360_final', 'IsSwitchGreen?'),
            caption=tester.translate('gsu360_final', 'capSwitchGreen'))
        self['o24Vocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_24V'],
            sensor=self['o24V'],
            detect_limit=(self.limits['24Vinocp'], ),
            start=15.0, stop=20.5, step=0.1, delay=0.1)
        self['o24Vocp'].reset = False


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_24V', '24V', 'o24V', ''),
            ('dmm_24Voff', '24Voff', 'o24V', ''),
            ('ui_YesNoGreen', 'Notify', 'oYesNoGreen', ''),
            ('ramp_24Vocp', '24Vocp', 'o24Vocp', ''),
            ))
