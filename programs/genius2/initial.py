#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Initial Test Program for GENIUS-II and GENIUS-II-H."""

import os
import inspect
import time
import tester
from tester import (
    TestStep,
    LimitLo, LimitHi, LimitHiLo, LimitHiLoDelta, LimitBoolean
    )
import share

PIC_HEX = 'genius2_3a.hex'

_OCP_LOW = 34.0
_OCP_HIGH = 43.0

_BASE_DATA = (
    LimitLo('DetectDiode', 0.3),
    LimitHiLoDelta('FlyLead', (30.0, 10.0)),
    LimitHiLoDelta('AcIn', (240.0, 5.0)),
    LimitHiLoDelta('Vbus', (330.0, 20.0)),
    LimitHiLo('Vcc', (13.8, 22.5)),
    LimitLo('VccOff', 5.0),
    LimitHiLoDelta('Vdd', (5.00, 0.1)),
    LimitHiLo('VbatCtl', (12.7, 13.5)),
    LimitHiLoDelta('Vctl', (12.0, 0.5)),
    LimitHiLo('VoutPre', (12.5, 15.0)),
    LimitHiLoDelta('Vout', (13.65, 0.05)),
    LimitLo('VoutOff', 1.0),
    LimitHiLo('VbatPre', (12.5, 15.0)),
    LimitHiLoDelta('Vbat', (13.65, 0.05)),
    LimitHiLoDelta('Vaux', (13.70, 0.5)),
    LimitLo('FanOff', 0.5),
    LimitHiLo('FanOn', (12.0, 14.1)),
    LimitLo('InOCP', 13.24),
    LimitHiLo('OCP', (_OCP_LOW, _OCP_HIGH)),
    LimitBoolean('Notify', True),
    LimitLo('FixtureLock', 20),
    )

LIMITS_STD = _BASE_DATA + (
    LimitLo('VbatOCP', 10.0),
    )

LIMITS_H = _BASE_DATA + (
    LimitHi('VbatOCP', 13.0),
    )

LIMITS = {      # Test limit selection keyed by program parameter
    'STD': {
        'Limits': LIMITS_STD,
        'LoadRatio': (29, 14),      # Iout:Ibat
        },
    'H': {
        'Limits': LIMITS_H,
        'LoadRatio': (5, 30),       # Iout:Ibat
        },
    }


class Initial(share.TestSequence):

    """GENIUS-II Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(
            LIMITS[self.parameter]['Limits'],
            LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Program', self._step_program, not self.fifo),
            TestStep('Aux', self._step_aux),
            TestStep('PowerUp', self._step_powerup),
            TestStep('VoutAdj', self._step_vout_adj),
            TestStep('ShutDown', self._step_shutdown),
            TestStep('OCP', self._step_ocp),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare: Dc input, measure."""
        dev['dcs_vaux'].output(12.0, output=True)
        self.dcload((('dcl_vbat', 0.4), ), output=True, delay=1.0)
        mes['dmm_diode'](timeout=5)
        self.dcload((('dcl_vbat', 0.0), ))
        self.dcsource(
            (('dcs_vaux', 0.0), ('dcs_vbatctl', 13.0), ), output=True)
        dev['rla_prog'].set_on()
        self.measure(('dmm_lock', 'dmm_vbatctl', 'dmm_vdd', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""
        dev['program_pic'].program()
        dev['dcs_vbatctl'].output(0.0, False)

    @share.teststep
    def _step_aux(self, dev, mes):
        """Aux: Dc input, measure."""
        dev['dcs_vaux'].output(13.8, output=True)
        self.dcload((('dcl', 0.1), ), output=True)
        self.measure(('dmm_voutpre', 'dmm_vaux', ), timeout=5)
        dev['dcs_vaux'].output(0.0, output=False)
        self.dcload((('dcl', 10.0), ), delay=2)
        self.dcload((('dcl', 0.0), ))

    @share.teststep
    def _step_powerup(self, dev, mes):
        """PowerUp: Check flying leads, AC input, measure."""
        dev['acsource'].output(30.0, output=True)
        mes['dmm_flyld'](timeout=5)
        dev['dcl'].output(0.1)
        dev['acsource'].output(voltage=240.0)
        self.measure(
            ('dmm_acin', 'dmm_vbus', 'dmm_vcc', 'dmm_vbatpre', 'dmm_voutpre',
             'dmm_vdd', 'dmm_vctl'),
            timeout=5)

    @share.teststep
    def _step_vout_adj(self, dev, mes):
        """Vout adjustment."""
        mes['ui_AdjVout'](timeout=5)
        dev['dcl'].output(2.0)
        self.measure(
            ('dmm_vout', 'dmm_vbatctl', 'dmm_vbat', 'dmm_vdd'), timeout=5)

    @share.teststep
    def _step_shutdown(self, dev, mes):
        """Shutdown."""
        mes['dmm_fanoff'](timeout=5)
        dev['rla_fan'].set_on()
        mes['dmm_fanon'](timeout=5)
        dev['rla_fan'].set_off()
        mes['dmm_vout'](timeout=5)
        dev['rla_shdwn2'].set_on()
        self.measure(('dmm_vccoff', 'dmm_voutoff', ), timeout=5)
        dev['rla_shdwn2'].set_off()
        mes['dmm_vout'](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Ramp up load until OCP."""
        # Check for correct model (GENIUS-II/GENIUS-II-H)
        dev['dcl_vbat'].binary(0.0, 18.0, 5.0)
        mes['dmm_vbatocp'](timeout=2)
        dev['dcl_vbat'].output(0.0)
        mes['dmm_vbat'](timeout=10)
        time.sleep(2)
        dev['dcl'].binary(0.0, _OCP_LOW - 2.0, 5.0)
        mes['ramp_OCP'].measure()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vout', tester.DCSource, 'DCS1'),
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcs_vaux', tester.DCSource, 'DCS4'),
                ('dcs_vbatctl', tester.DCSource, 'DCS5'),
                ('dcl_vout', tester.DCLoad, 'DCL1'),
                ('dcl_vbat', tester.DCLoad, 'DCL5'),
                ('rla_prog', tester.Relay, 'RLA1'),
                ('rla_vbus', tester.Relay, 'RLA2'),
                ('rla_batfuse', tester.Relay, 'RLA3'),
                ('rla_fan', tester.Relay, 'RLA5'),
                ('rla_shdwn1', tester.Relay, 'RLA6'),
                ('rla_shdwn2', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        r_out, r_bat = LIMITS[self.parameter]['LoadRatio']
        self['dcl'] = tester.DCLoadParallel(
            ((self['dcl_vout'], r_out), (self['dcl_vbat'], r_bat)))
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_pic'] = share.ProgramPIC(
            PIC_HEX, folder, '16F1828', self['rla_prog'])

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source & discharge the unit
        self['acsource'].output(voltage=0.0, output=False)
        self['dcl'].output(10.0)
        time.sleep(1)
        self['discharge'].pulse()
        for dev in (
                'dcs_vout', 'dcs_vbat', 'dcs_vaux', 'dcs_vbatctl', 'dcl'):
            self[dev].output(0.0, False)
        for rla in (
                'rla_prog', 'rla_vbus', 'rla_batfuse',
                'rla_fan', 'rla_shdwn1', 'rla_shdwn2'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['diode'] = sensor.Vdc(dmm, high=7, low=8, rng=10, res=0.001)
        self['olock'] = sensor.Res(dmm, high=16, low=4, rng=10000, res=1)
        self['oacin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['oflyld'] = sensor.Vac(dmm, high=15, low=7, rng=1000, res=0.01)
        self['ovcap'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self['ovbus'] = sensor.Vdc(dmm, high=3, low=2, rng=1000, res=0.01)
        self['ovcc'] = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.001)
        self['ovout'] = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.001)
        self['ovbat'] = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self['ovaux'] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self['ovbatfuse'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self['ovctl'] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self['ovbatctl'] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self['ovdd'] = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self['ofan'] = sensor.Vdc(dmm, high=13, low=5, rng=100, res=0.01)
        self['oshdwn'] = sensor.Vdc(dmm, high=14, low=6, rng=100, res=0.01)
        lo_lim, hi_lim = self.limits['Vout'].limit
        self['oAdjVout'] = sensor.AdjustAnalog(
            sensor=self['ovout'],
            low=lo_lim, high=hi_lim,
            message=tester.translate('GENIUS-II Initial', 'AdjR39'),
            caption=tester.translate('GENIUS-II Initial', 'capAdjVout'))
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl'], sensor=self['ovout'],
            detect_limit=(self.limits['InOCP'], ),
            start=_OCP_LOW - 1.0, stop=_OCP_HIGH + 1.0, step=0.2)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_diode', 'DetectDiode', 'diode'),
            ('dmm_lock', 'FixtureLock', 'olock'),
            ('dmm_flyld', 'FlyLead', 'oflyld'),
            ('dmm_acin', 'AcIn', 'oacin'),
            ('dmm_vbus', 'Vbus', 'ovbus'),
            ('dmm_vcc', 'Vcc', 'ovcc'),
            ('dmm_vccoff', 'VccOff', 'ovcc'),
            ('dmm_vdd', 'Vdd', 'ovdd'),
            ('dmm_vbatctl', 'VbatCtl', 'ovbatctl'),
            ('dmm_vctl', 'Vctl', 'ovctl'),
            ('dmm_voutpre', 'VoutPre', 'ovout'),
            ('dmm_vout', 'Vout', 'ovout'),
            ('dmm_voutoff', 'VoutOff', 'ovout'),
            ('dmm_vbatpre', 'VbatPre', 'ovbat'),
            ('dmm_vbat', 'Vbat', 'ovbat'),
            ('dmm_vbatocp', 'VbatOCP', 'ovbat'),
            ('dmm_vaux', 'Vaux', 'ovaux'),
            ('dmm_fanoff', 'FanOff', 'ofan'),
            ('dmm_fanon', 'FanOn', 'ofan'),
            ('ui_AdjVout', 'Notify', 'oAdjVout'),
            ('ramp_OCP', 'OCP', 'oOCP'),
            ))
