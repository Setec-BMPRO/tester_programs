#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Test Program for GENIUS-II and GENIUS-II-H."""

import tester
from tester import TestStep, LimitLow, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """GENIUS-II Final Test Program."""

    # Common test limits
    _common = (
        LimitBetween('InRes', 80e3, 170e3),
        LimitDelta('Vout', 13.675, 0.1),
        LimitLow('VoutOff', 2.0),
        LimitBetween('VoutStartup', 13.60, 14.10),
        LimitDelta('Vbat', 13.675, 0.1),
        LimitLow('VbatOff', 1.0),
        LimitBetween('ExtBatt', 11.5, 12.8),
        LimitLow('InOCP', 13.24),
        LimitBetween('OCP', 34.0, 43.0),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        'STD': {
            'Limits': _common,
            'MaxBattLoad': 15.0,
            'LoadRatio': (29, 14),      # Vout:Vbat load ratio
            },
        'H': {
            'Limits': _common,
            'MaxBattLoad': 30.0,
            'LoadRatio': (5, 30),       # Vout:Vbat load ratio
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('InputRes', self._step_inres),
            TestStep('PowerOn', self._step_poweron),
            TestStep('BattFuse', self._step_battfuse),
            TestStep('OCP', self._step_ocp),
            TestStep('RemoteSw', self._step_remote_sw),
            )

    @share.teststep
    def _step_inres(self, dev, mes):
        """Verify that the hand loaded input discharge resistors are there."""
        mes['dmm_InpRes'](timeout=5)

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Switch on unit at 240Vac, no load."""
        dev['acsource'].output(240.0, output=True)
        self.measure(('dmm_Vout', 'dmm_Vbat'), timeout=10)

    @share.teststep
    def _step_battfuse(self, dev, mes):
        """Remove and insert battery fuse, check red LED."""
        self.measure(
            ('ui_YesNoFuseOut', 'dmm_VbatOff', 'ui_YesNoFuseIn', 'dmm_Vout'),
            timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Ramp up load until OCP, shutdown and recover."""
        dev['dcl'].output(0.0, output=True)
        dev['dcl'].binary(0.0, 32.0, 5.0)
        mes['ramp_OCP']()
        dev['dcl'].output(47.0)
        mes['dmm_VoutOff'](timeout=10)
        dev['dcl'].output(0.0)
        self.measure(('dmm_VoutStartup', 'dmm_Vout', 'dmm_Vbat',), timeout=10)

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Switch off AC, apply external Vbat, remote switch."""
        dev['acsource'].output(0.0)
        dev['dcl'].output(2.0, output=True, delay=1)
        dev['dcl'].output(0.1)
        dev['dcs_vbat'].output(12.6, output=True, delay=2)
        self.measure(('dmm_VbatExt', 'dmm_VoutExt', ), timeout=5)
        dev['rla_RemoteSw'].set_on()
        mes['dmm_VoutOff'](timeout=10)
        dev['rla_RemoteSw'].set_off()
        mes['dmm_VoutExt'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                # This DC Source simulates the battery voltage
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcl_vout', tester.DCLoad, 'DCL1'),
                ('dcl_vbat', tester.DCLoad, 'DCL3'),
                ('rla_RemoteSw', tester.Relay, 'RLA1')
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        ratio_vout, ratio_vbat = Final.limitdata[self.parameter]['LoadRatio']
        self['dcl'] = tester.DCLoadParallel(
            ((self['dcl_vout'], ratio_vout),
             (self['dcl_vbat'], ratio_vbat), )
            )

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl'].output(0.0)
        self['dcs_vbat'].output(0.0, False)
        self['rla_RemoteSw'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oInpRes'] = sensor.Res(dmm, high=1, low=1, rng=1e6, res=1)
        self['oVout'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['oVbat'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['oVout'],
            detect_limit=(self.limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self['oYesNoFuseOut'] = sensor.YesNo(
            message=tester.translate(
                'geniusII_final', 'RemoveBattFuseIsLedRedFlashing?'),
            caption=tester.translate('geniusII_final', 'capLedRed'))
        self['oYesNoFuseIn'] = sensor.YesNo(
            message=tester.translate(
                'geniusII_final', 'ReplaceBattFuseIsLedGreen?'),
            caption=tester.translate('geniusII_final', 'capLedRed'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_InpRes', 'InRes', 'oInpRes', ''),
            ('dmm_Vout', 'Vout', 'oVout', ''),
            ('dmm_VoutOff', 'VoutOff', 'oVout', ''),
            ('dmm_VoutStartup', 'VoutStartup', 'oVout', ''),
            ('dmm_VoutExt', 'ExtBatt', 'oVout', ''),
            ('dmm_Vbat', 'Vbat', 'oVbat', ''),
            ('dmm_VbatOff', 'VbatOff', 'oVbat', ''),
            ('dmm_VbatExt', 'ExtBatt', 'oVbat', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ('ui_YesNoFuseOut', 'Notify', 'oYesNoFuseOut', ''),
            ('ui_YesNoFuseIn', 'Notify', 'oYesNoFuseIn', ''),
            ))
