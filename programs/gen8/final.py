#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Final Test Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitBoolean, LimitBetween, LimitDelta
    )
import share

LIMITS = (
    LimitDelta('Iecon', 240, 10),
    LimitLow('Iecoff', 10),
    LimitBetween('5V', 4.998, 5.202),
    LimitLow('24Voff', 0.5),
    LimitLow('12Voff', 0.5),
    LimitLow('12V2off', 0.5),
    LimitBetween('24Von', 22.80, 25.44),
    LimitBetween('12Von', 11.8755, 12.4845),
    LimitBetween('12V2on', 11.8146, 12.4845),
    LimitHigh('PwrFailOff', 11.0),
    LimitBoolean('Notify', True),
    )


class Final(share.TestSequence):

    """GEN8 Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_pwrup),
            TestStep('PowerOn', self._step_pwron),
            TestStep('FullLoad', self._step_fullload),
            TestStep('115V', self._step_fullload115),
            TestStep('Poweroff', self._step_pwroff),
            )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power Up step."""
        self.dcload(
            (('dcl_5v', 0.0), ('dcl_24v', 0.1), ('dcl_12v', 3.5),
             ('dcl_12v2', 0.5), ), output=True)
        dev['acsource'].output(voltage=240.0, output=True, delay=1.0)
        self.measure(('dmm_5v', 'dmm_24voff', 'dmm_12voff', ), timeout=5)
        dev['rla_12v2off'].set_on()
        mes['dmm_12v2off'](timeout=5)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power On step."""
        dev['rla_pson'].set_on()
        self.measure(
            ('dmm_24von', 'dmm_12von', 'dmm_12v2off', 'dmm_pwrfailoff', ),
            timeout=5)
        dev['rla_12v2off'].set_off()
        self.measure(('dmm_12v2on', 'dmm_iec_on', ), timeout=5)
        mes['ui_yesno_mains']()

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        self.dcload(
            (('dcl_5v', 2.5), ('dcl_24v', 5.0), ('dcl_12v', 15.0),
             ('dcl_12v2', 7.0), ), delay=0.5)
        self.measure(
            ('dmm_5v', 'dmm_24von', 'dmm_12von', 'dmm_12v2on', ), timeout=5)

    @share.teststep
    def _step_fullload115(self, dev, mes):
        """115Vac step."""
        dev['acsource'].output(voltage=115.0, delay=0.5)
        self.measure(
            ('dmm_5v', 'dmm_24von', 'dmm_12von', 'dmm_12v2on', ), timeout=5)

    @share.teststep
    def _step_pwroff(self, dev, mes):
        """Power Off step."""
        self.dcload((('dcl_5v', 0.5), ('dcl_24v', 0.5), ('dcl_12v', 4.0), ))
        self.measure(('ui_notify_pwroff', 'dmm_iec_off', 'dmm_24voff', ))


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_24v', tester.DCLoad, 'DCL1'),
                ('dcl_12v', tester.DCLoad, 'DCL2'),
                ('dcl_12v2', tester.DCLoad, 'DCL3'),
                ('dcl_5v', tester.DCLoad, 'DCL4'),
                ('rla_12v2off', tester.Relay, 'RLA2'),
                ('rla_pson', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].output(voltage=0.0, output=False)
        for load in ('dcl_12v', 'dcl_24v', 'dcl_5v', 'dcl_12v2'):
            self[load].output(0.0, False)
        for rla in ('rla_12v2off', 'rla_pson'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['iec'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['o5v'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self['o24v'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['o12v'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o12v2'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['pwrfail'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self['yn_mains'] = sensor.YesNo(
            message=tester.translate('gen8_final', 'IsSwitchGreen?'),
            caption=tester.translate('gen8_final', 'capSwitchGreen'))
        self['not_pwroff'] = sensor.Notify(
            message=tester.translate('gen8_final', 'msgSwitchOff'),
            caption=tester.translate('gen8_final', 'capSwitchOff'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_iec_on', 'Iecon', 'iec'),
            ('dmm_iec_off', 'Iecoff', 'iec'),
            ('dmm_5v', '5V', 'o5v'),
            ('dmm_24voff', '24Voff', 'o24v'),
            ('dmm_12voff', '12Voff', 'o12v'),
            ('dmm_12v2off', '12V2off', 'o12v2'),
            ('dmm_24von', '24Von', 'o24v'),
            ('dmm_12von', '12Von', 'o12v'),
            ('dmm_12v2on', '12V2on', 'o12v2'),
            ('dmm_pwrfailoff', 'PwrFailOff', 'pwrfail'),
            ('ui_yesno_mains', 'Notify', 'yn_mains'),
            ('ui_notify_pwroff', 'Notify', 'not_pwroff'),
            ))
