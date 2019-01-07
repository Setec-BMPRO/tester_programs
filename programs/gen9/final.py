#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""GEN9-540 Final Test Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitPercent, LimitDelta,
    )
import share


class Final(share.TestSequence):

    """GEN9-540 Final Test Program."""

    limitdata = (
        LimitLow('FanOff', 9.0, doc='Airflow not present'),
        LimitHigh('FanOn', 11.0, doc='Airflow present'),
        LimitDelta('GPO1out', 240, 10, doc='Voltage present'),
        LimitDelta('GPO2out', 240, 10, doc='Voltage present'),
        LimitPercent('5V', 5.10, 2.0, doc='5V output ok'),
        LimitLow('12Voff', 0.5, doc='12V output off'),
        LimitPercent('12V', 12.0, 2.5, doc='12V output ok'),
        LimitLow('24Voff', 0.5, doc='24V output off'),
        LimitPercent('24V', 24.0, 2.5, doc='24V output ok'),
        LimitLow('PwrFail', 0.4, doc='PFAIL asserted'),
        LimitHigh('PwrFailOff', 11.0, doc='PFAIL not asserted'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_pwrup),
            TestStep('PowerOn', self._step_pwron),
            TestStep('FullLoad', self._step_fullload),
            )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power Up step."""
        mes['dmm_fanoff'](timeout=5)
        dev['acsource'].output(240.0, output=True)
        self.dcload(
            (('dcl_5v', 0.1), ('dcl_24v', 1.0), ('dcl_12v', 1.0)),
             output=True, delay=0.5)
        self.measure(
            ('dmm_5v', 'dmm_12voff', 'dmm_24voff', 'dmm_pwrfail'), timeout=10)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power On step."""
        self.dcload((('dcl_5v', 0.0), ('dcl_24v', 0.0), ('dcl_12v', 0.0)))
        dev['rla_pson'].set_on()
        mes['dmm_fanon'](timeout=15)
        self.measure(
            ('dmm_12v', 'dmm_24v', 'dmm_pwrfailoff', 'dmm_gpo1',
             'dmm_gpo2'), timeout=5)

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        self.dcload(
            (('dcl_5v', 2.0), ('dcl_24v', 10.0), ('dcl_12v', 24.0)),
             delay=0.5)
        self.measure(('dmm_5v', 'dmm_24v', 'dmm_12v'), timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname, doc in (
                ('dmm', tester.DMM, 'DMM', ''),
                ('acsource', tester.ACSource, 'ACS', 'AC Input'),
                ('dcl_24v', tester.DCLoad, 'DCL3', '24V Load'),
                ('dcl_12a', tester.DCLoad, 'DCL2', '12V Load'),
                ('dcl_12b', tester.DCLoad, 'DCL6', '12V Load'),
                ('dcl_5v', tester.DCLoad, 'DCL4', '5V Load'),
                ('rla_pson', tester.Relay, 'RLA3', 'PSON control'),
                ('dcs_airflow', tester.DCSource, 'DCS3',
                 'Power to airflow detector'),
            ):
            self[name] = devtype(self.physical_devices[phydevname], doc)
        self['dcl_12v'] = tester.DCLoadParallel(
            ((self['dcl_12a'], 10), (self['dcl_12b'], 10)))
        self['dcs_airflow'].output(12.0, True)
        self.add_closer(lambda: self['dcs_airflow'].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source and discharge the unit
        self['acsource'].reset()
        self['dcl_5v'].output(1.0)
        self['dcl_12v'].output(5.0)
        self['dcl_24v'].output(5.0, delay=1.0)
        for ld in ('dcl_12v', 'dcl_24v', 'dcl_5v'):
            self[ld].output(0.0, False)
        self['rla_pson'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['gpo1'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['gpo2'] = sensor.Vac(dmm, high=8, low=4, rng=1000, res=0.01)
        self['airflow'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self['airflow'].doc = 'Airflow detector'
        self['o5v'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self['o12v'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o24v'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['pwrfail'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_fanoff', 'FanOff', 'airflow', 'Fan not running'),
            ('dmm_fanon', 'FanOn', 'airflow', 'Fan running'),
            ('dmm_gpo1', 'GPO1out', 'gpo1', 'GPO1 output ON'),
            ('dmm_gpo2', 'GPO2out', 'gpo2', 'GPO2 output ON'),
            ('dmm_5v', '5V', 'o5v', '5V output ok'),
            ('dmm_12voff', '12Voff', 'o12v', '12V output off'),
            ('dmm_12v', '12V', 'o12v', '12V output ok'),
            ('dmm_24voff', '24Voff', 'o24v', '24V output off'),
            ('dmm_24v', '24V', 'o24v', '24V output ok'),
            ('dmm_pwrfail', 'PwrFail', 'pwrfail', 'PFAIL asserted'),
            ('dmm_pwrfailoff', 'PwrFailOff', 'pwrfail', 'PFAIL not asserted'),
            ))
