#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STxx-III Final Test Program."""

import time
import tester
from tester import TestStep, LimitLow, LimitBetween, LimitRegExp
import share


class Final(share.TestSequence):

    """STxx-III Final Test Program."""

    # Test limits common to both versions
    _common = (
        LimitLow('Voff', 2.0),
        LimitBetween('Vout', 13.60, 13.70),
        LimitBetween('Vbat', 13.40, 13.70),
        LimitBetween('Vtrickle', 3.90, 5.70),
        LimitBetween('Vboost', 13.80, 14.10),
        LimitLow('inOCP', 11.6),
        LimitLow('FuseOut', 0.5),
        LimitBetween('FuseIn', 13.60, 13.70),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        '20': {
            'Limits': _common + (
                LimitBetween('LoadOCP', 20.5, 26.0),
                LimitBetween('BattOCP', 9.0, 11.5),
                LimitRegExp('FuseLabel', '^ST20\-III$'),
                ),
            'FullLoad': 20.1,
            'LoadOCPramp': (19.5, 28.0),
            'BattOCPramp': (8.0, 13.5),
            },
        '35': {
            'Limits': _common + (
                LimitBetween('LoadOCP', 35.1, 42.5),
                LimitBetween('BattOCP', 14.0, 17.0),
                LimitRegExp('FuseLabel', '^ST35\-III$'),
                ),
            'FullLoad': 35.1,
            'LoadOCPramp': (34.1, 43.5),
            'BattOCPramp': (13.0, 19.0),
            },
        }

    def open(self):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('FuseLabel', self._step_label),
            TestStep('PowerUp', self._step_power_up),
            TestStep('Battery', self._step_battery),
            TestStep('LoadOCP', self._step_load_ocp),
            TestStep('BattOCP', self._step_batt_ocp),
            )

    @share.teststep
    def _step_label(self, dev, mes):
        """Check Fuse Label."""
        mes['barcode']()

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit."""
        dev['acsource'].output(240.0, output=True)
        self.measure(
            ('dmm_Boost',
             'dmm_Fuse1', 'dmm_Fuse2', 'dmm_Fuse3', 'dmm_Fuse4',
             'dmm_Fuse5', 'dmm_Fuse6', 'dmm_Fuse7', 'dmm_Fuse8',
             'dmm_Batt', 'ui_YesNoOrGr', ),
            timeout=10)

    @share.teststep
    def _step_battery(self, dev, mes):
        """Battery checks."""
        self.dcload((('dcl_Batt', 2.0), ('dcl_Load', 0.0), ), output=True)
        dev['rla_BattSw'].set_on()
        mes['dmm_BattFuseOut'](timeout=5)
        dev['dcl_Batt'].output(0.0)
        dev['rla_BattSw'].set_off(delay=0.5)
        self.measure(
            ('dmm_BattFuseIn', 'ui_YesNoRedOn', 'ui_YesNoRedOff', ),
            timeout=5)

    @share.teststep
    def _step_load_ocp(self, dev, mes):
        """Measure Load OCP point."""
        mes['ramp_LoadOCP']()
        dev['dcl_Load'].output(
            self.limitdata[self.parameter]['FullLoad'] * 1.30)
        mes['dmm_Overload'](timeout=5)
        dev['dcl_Load'].output(0.0)
        mes['dmm_Load'](timeout=10)
        time.sleep(1)

    @share.teststep
    def _step_batt_ocp(self, dev, mes):
        """Measure Batt OCP point."""
        mes['ramp_BattOCP']()
        dev['dcl_Batt'].output(0.1)
        mes['dmm_Batt'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_Load', tester.DCLoad, 'DCL1'),
                ('dcl_Batt', tester.DCLoad, 'DCL5'),
                ('rla_BattSw', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_Load'].output(5.0, True, delay=0.5)
        for dcl in ('dcl_Load', 'dcl_Batt'):
            self[dcl].output(0.0, False)
        self['rla_BattSw'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oLoad'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self['oFuse1'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self['oFuse2'] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.001)
        self['oFuse3'] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self['oFuse4'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self['oFuse5'] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self['oFuse6'] = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.001)
        self['oFuse7'] = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self['oFuse8'] = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self['oBatt'] = sensor.Vdc(dmm, high=9, low=2, rng=100, res=0.001)
        self['oAlarm'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self['oBarcode'] = sensor.DataEntry(
            message=tester.translate('st3_final', 'ScanBarcode'),
            caption=tester.translate('st3_final', 'capBarcode'))
        self['oYesNoOrGr'] = sensor.YesNo(
            message=tester.translate('st3_final', 'AreOrangeGreen?'),
            caption=tester.translate('st3_final', 'capOrangeGreen'))
        self['oYesNoRedOn'] = sensor.YesNo(
            message=tester.translate('st3_final', 'RemoveBattFuseIsRedBlink?'),
            caption=tester.translate('st3_final', 'capRed'))
        self['oYesNoRedOff'] = sensor.YesNo(
            message=tester.translate('st3_final', 'ReplaceBattFuseIsRedOff?'),
            caption=tester.translate('st3_final', 'capRed'))
        ocp_start, ocp_stop = Final.limitdata[self.parameter]['LoadOCPramp']
        self['oLoadOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_Load'],
            sensor=self['oLoad'],
            detect_limit=(self.limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1, reset=False)
        ocp_start, ocp_stop = Final.limitdata[self.parameter]['BattOCPramp']
        self['oBattOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_Batt'],
            sensor=self['oBatt'],
            detect_limit=(self.limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('barcode', 'FuseLabel', 'oBarcode', ''),
            ('dmm_Load', 'Vout', 'oLoad', ''),
            ('dmm_Boost', 'Vboost', 'oLoad', ''),
            ('dmm_Batt', 'Vbat', 'oBatt', ''),
            ('dmm_Fuse1', 'FuseIn', 'oFuse1', ''),
            ('dmm_Fuse2', 'FuseIn', 'oFuse2', ''),
            ('dmm_Fuse3', 'FuseIn', 'oFuse3', ''),
            ('dmm_Fuse4', 'FuseIn', 'oFuse4', ''),
            ('dmm_Fuse5', 'FuseIn', 'oFuse5', ''),
            ('dmm_Fuse6', 'FuseIn', 'oFuse6', ''),
            ('dmm_Fuse7', 'FuseIn', 'oFuse7', ''),
            ('dmm_Fuse8', 'FuseIn', 'oFuse8', ''),
            ('ui_YesNoOrGr', 'Notify', 'oYesNoOrGr', ''),
            ('ui_YesNoRedOn', 'Notify', 'oYesNoRedOn', ''),
            ('ui_YesNoRedOff', 'Notify', 'oYesNoRedOff', ''),
            ('dmm_BattFuseOut', 'FuseOut', 'oBatt', ''),
            ('dmm_BattFuseIn', 'FuseIn', 'oBatt', ''),
            ('ramp_LoadOCP', 'LoadOCP', 'oLoadOCP', ''),
            ('dmm_Overload', 'Voff', 'oLoad', ''),
            ('ramp_BattOCP', 'BattOCP', 'oBattOCP', ''),
            ))
