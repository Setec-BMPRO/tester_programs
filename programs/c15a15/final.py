#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Final Test Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitBoolean, LimitBetween, LimitDelta
    )
import share

LIMITS = (
    LimitDelta('Vout', 15.5, 0.3),
    LimitLow('Voutfl', 5.0),
    LimitBetween('OCP', 1.0, 1.4),
    LimitLow('inOCP', 13.6),
    LimitBoolean('Notify', True),
    )

# Resistive loading during OCP
ILOAD = 1.0


class Final(share.TestSequence):

    """C15A-15 Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('OCP', self._step_ocp),
            TestStep('FullLoad', self._step_full_load),
            TestStep('PowerOff', self._step_power_off),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """
        Power up with 240Vac, measure output, check Green and Yellow leds.
        """
        dev['acsource'].output(240.0, output=True, delay=0.5)
        dev['dcl'].output(0.0, output=True)
        self.measure(
            ('dmm_Vout', 'ui_YesNoGreen', 'ui_YesNoYellowOff',
            'ui_NotifyYellow', ), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP."""
        dev['rla_load'].set_on()
        mes['ramp_OCP']()
        dev['rla_load'].set_off()
        self.measure(('ui_YesNoYellowOn', 'dmm_Vout',), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure output at full load and after recovering."""
        dev['dcl'].output(1.31, output=True)
        mes['dmm_Voutfl'](timeout=5)
        dev['dcl'].output(0.0)
        mes['dmm_Vout'](timeout=5)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Input AC off and discharge."""
        dev['dcl'].output(1.0)
        dev['acsource'].output(0.0, delay=2)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl', tester.DCLoad, 'DCL5'),
                ('rla_load', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl'].output(0.0, False)
        self['rla_load'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oVout'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self['oYesNoGreen'] = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsPowerLedGreen?'),
            caption=tester.translate('c15a15_final', 'capPowerLed'))
        self['oYesNoYellowOff'] = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsYellowLedOff?'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self['oNotifyYellow'] = sensor.Notify(
            message=tester.translate('c15a15_final', 'WatchYellowLed'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self['oYesNoYellowOn'] = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsYellowLedOn?'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl'], sensor=self['oVout'],
            detect_limit=(self.limits['inOCP'], ),
            start=0.0, stop=0.5, step=0.05, delay=0.2)
        self['oOCP'].on_read = lambda value: value + ILOAD


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_Vout', 'Vout', 'oVout', ''),
            ('dmm_Voutfl', 'Voutfl', 'oVout', ''),
            ('ui_YesNoGreen', 'Notify', 'oYesNoGreen', ''),
            ('ui_YesNoYellowOff', 'Notify', 'oYesNoYellowOff', ''),
            ('ui_NotifyYellow', 'Notify', 'oNotifyYellow', ''),
            ('ui_YesNoYellowOn', 'Notify', 'oYesNoYellowOn', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ))
