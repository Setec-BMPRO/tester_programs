#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MK7-400-1 Final Test Program."""

import tester
from tester import TestStep, LimitLow, LimitHigh, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """MK7-400-1 Final Test Program."""

    limits = (
        LimitDelta('ACon', 240, 10),
        LimitLow('ACoff', 10),
        LimitDelta('5V', 5.00, 0.25),
        LimitLow('12Voff', 0.5),
        LimitBetween('12Von', 12.0, 12.6),
        LimitLow('24Voff', 0.5),
        LimitDelta('24Von', 24.0, 0.6),
        LimitLow('24V2off', 0.5),
        LimitDelta('24V2on', 24.0, 0.6),
        LimitHigh('PwrFailOff', 11.0),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limits, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('PowerOn', self._step_power_on),
            TestStep('FullLoad', self._step_full_load),
            TestStep('115V', self._step_115v),
            TestStep('Poweroff', self._step_power_off),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """
        Switch on unit at 240Vac, not enabled.

        Measure output voltages at min load.

        """
        dev['rla_24V2off'].set_on()
        self.dcload(
            (('dcl_5V', 0.5), ('dcl_12V', 0.5), ('dcl_24V', 0.5),
             ('dcl_24V2', 0.5), ), output=True)
        dev['acsource'].output(240.0, output=True, delay=0.5)
        self.measure(
            ('dmm_5V', 'dmm_24Voff', 'dmm_12Voff', 'dmm_24V2off', ),
            timeout=5)

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Enable outputs, measure voltages at min load."""
        dev['rla_pson'].set_on()
        self.measure(
            ('dmm_24Von', 'dmm_12Von', 'dmm_24V2off', 'dmm_PwrFailOff', ),
            timeout=5)
        dev['rla_24V2off'].set_off()
        self.measure(('dmm_24V2on', 'dmm_AuxOn', 'dmm_AuxSwOn', ), timeout=5)
        mes['ui_YesNoMains']()

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        self.dcload(
            (('dcl_5V', 2.0), ('dcl_12V', 10.0),
             ('dcl_24V', 6.5), ('dcl_24V2', 4.5), ))
        self.measure(
            ('dmm_5V', 'dmm_24Von', 'dmm_12Von', 'dmm_24V2on', ), timeout=5)

    @share.teststep
    def _step_115v(self, dev, mes):
        """Measure outputs at 115Vac in, full-load."""
        dev['acsource'].output(115.0, delay=0.5)
        self.measure(
            ('dmm_5V', 'dmm_24Von', 'dmm_12Von', 'dmm_24V2on', ), timeout=5)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Switch off unit, measure Aux and 24V voltages."""
        self.dcload(
            (('dcl_5V', 0.5), ('dcl_12V', 0.5),
             ('dcl_24V', 0.5), ('dcl_24V2', 0.5), ))
        self.measure(
            ('ui_NotifyPwrOff', 'dmm_AuxOff', 'dmm_AuxSwOff', 'dmm_24Voff', ))


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_24V', tester.DCLoad, 'DCL1'),
                ('dcl_12V', tester.DCLoad, 'DCL2'),
                ('dcl_24V2', tester.DCLoad, 'DCL3'),
                ('dcl_5V', tester.DCLoad, 'DCL4'),
                ('rla_24V2off', tester.Relay, 'RLA2'),
                ('rla_pson', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        for load in ('dcl_12V', 'dcl_24V', 'dcl_5V', 'dcl_24V2'):
            self[load].output(0.0, False)
        for rla in ('rla_24V2off', 'rla_pson'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oAux'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['oAuxSw'] = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self['o5V'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self['o24V'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['o12V'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o24V2'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['oPwrFail'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self['oYesNoMains'] = sensor.YesNo(
            message=tester.translate('mk7_final', 'IsSwitchLightOn?'),
            caption=tester.translate('mk7_final', 'capSwitchLight'))
        self['oNotifyPwrOff'] = sensor.Notify(
            message=tester.translate('mk7_final', 'msgSwitchOff'),
            caption=tester.translate('mk7_final', 'capSwitchOff'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_AuxOn', 'ACon', 'oAux', ''),
            ('dmm_AuxOff', 'ACoff', 'oAux', ''),
            ('dmm_AuxSwOn', 'ACon', 'oAuxSw', ''),
            ('dmm_AuxSwOff', 'ACoff', 'oAuxSw', ''),
            ('dmm_5V', '5V', 'o5V', ''),
            ('dmm_12Voff', '12Voff', 'o12V', ''),
            ('dmm_24Voff', '24Voff', 'o24V', ''),
            ('dmm_24V2off', '24V2off', 'o24V2', ''),
            ('dmm_12Von', '12Von', 'o12V', ''),
            ('dmm_24Von', '24Von', 'o24V', ''),
            ('dmm_24V2on', '24V2on', 'o24V2', ''),
            ('dmm_PwrFailOff', 'PwrFailOff', 'oPwrFail', ''),
            ('ui_YesNoMains', 'Notify', 'oYesNoMains', ''),
            ('ui_NotifyPwrOff', 'Notify', 'oNotifyPwrOff', ''),
            ))
