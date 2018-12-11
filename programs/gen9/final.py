#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""GEN9-540 Final Test Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitBetween, LimitPercent, LimitDelta,
    )
import share


class Final(share.TestSequence):

    """GEN9-540 Final Test Program."""

    limitdata = (
        LimitLow('FanOff', 1.0, doc='Airflow present'),
        LimitHigh('FanOn', 10.0, doc='Airflow not present'),
        LimitDelta('Iecon', 240, 10, doc='Voltage present'),
        LimitLow('Iecoff', 10, doc='Voltage off'),
        LimitBetween('5V', 4.998, 5.202, doc='5V output ok'),
        LimitLow('24Voff', 0.5, doc='24V output off'),
        LimitLow('12Voff', 0.5, doc='12V output off'),
        LimitPercent('24Von', 24.0, 2.5, doc='24V output ok'),
        LimitPercent('12Von', 12.0, 2.5, doc='12V output ok'),
        LimitHigh('PwrFailOff', 11.0, doc='PFAIL not asserted'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
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
            (('dcl_5v', 0.0), ('dcl_24v', 0.1), ('dcl_12v', 1.0)), output=True)
        mes['dmm_fanoff'](timeout=5)
        dev['acsource'].output(240.0, output=True)
        mes['dmm_fanon'](timeout=15)
        self.measure(('dmm_5v', 'dmm_24voff', 'dmm_12voff'), timeout=5)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power On step."""
        dev['rla_pson'].set_on()
        self.measure(('dmm_24von', 'dmm_12von', 'dmm_pwrfailoff'), timeout=5)
        self.measure(('dmm_iec_on', 'ui_yesno_mains', ), timeout=5)

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        self.dcload(
            (('dcl_5v', 2.5), ('dcl_24v', 10.0), ('dcl_12v', 24.0)), delay=0.5)
        self.measure(('dmm_5v', 'dmm_24von', 'dmm_12von'), timeout=5)

    @share.teststep
    def _step_fullload115(self, dev, mes):
        """115Vac step."""
        dev['acsource'].output(voltage=115.0, delay=0.5)
        self.measure(('dmm_5v', 'dmm_24von', 'dmm_12von'), timeout=5)

    @share.teststep
    def _step_pwroff(self, dev, mes):
        """Power Off step."""
        self.dcload((('dcl_5v', 0.5), ('dcl_24v', 0.5), ('dcl_12v', 4.0), ))
        self.measure(('ui_notify_pwroff', 'dmm_iec_off', 'dmm_24voff', ))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname, doc in (
                ('dmm', tester.DMM, 'DMM', ''),
                ('acsource', tester.ACSource, 'ACS', 'AC Input'),
                ('dcl_24v', tester.DCLoad, 'DCL1', '24V Load'),
                ('dcl_12v', tester.DCLoad, 'DCL2', '12V Load'),
                ('dcl_5v', tester.DCLoad, 'DCL4', '5V Load'),
                ('rla_pson', tester.Relay, 'RLA3', 'PSON control'),
                ('dcs_airflow', tester.DCSource, 'DCS3',
                 'Power to airflow detector'),
            ):
            self[name] = devtype(self.physical_devices[phydevname], doc)
        self['dcs_airflow'].output(12.0, True)
        self.add_closer(lambda: self['dcs_airflow'].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        for ld in ('dcl_12v', 'dcl_24v', 'dcl_5v'):
            self[ld].output(0.0, False)
        self['rla_pson'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['iec'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['airflow'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self['airflow'].doc = 'Airflow detector'
        self['o5v'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self['o24v'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['o12v'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
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
            ('dmm_fanoff', 'FanOff', 'airflow', 'Fan not running'),
            ('dmm_fanon', 'FanOn', 'airflow', 'Fan running'),
            ('dmm_iec_on', 'Iecon', 'iec', 'IEC output ON'),
            ('dmm_iec_off', 'Iecoff', 'iec', 'IEC output OFF'),
            ('dmm_5v', '5V', 'o5v', '5V output ok'),
            ('dmm_24voff', '24Voff', 'o24v', '24V output off'),
            ('dmm_12voff', '12Voff', 'o12v', '12V output off'),
            ('dmm_24von', '24Von', 'o24v', '24V output ok'),
            ('dmm_12von', '12Von', 'o12v', '12V output ok'),
            ('dmm_pwrfailoff', 'PwrFailOff', 'pwrfail', 'PFAIL not asserted'),
            ('ui_yesno_mains', 'Notify', 'yn_mains', ''),
            ('ui_notify_pwroff', 'Notify', 'not_pwroff', ''),
            ))
