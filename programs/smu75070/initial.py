#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""SMU750-70 Initial Test Program."""
import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitBoolean, LimitBetween, LimitPercent, LimitDelta
    )
import share

# Load reg of output (%)
VOUT_LOAD_REG = 0.4

LIMITS = (
    LimitLow('FixtureLock', 200, doc='Closed micro switch'),
    LimitBetween('InrushOff', 120, 180,
        doc='Inrush resistors with K1 off'),
    LimitBetween('VacMin', 95.0, 105.0, doc='Min AC input voltage'),
    LimitBetween('Vac', 237.0, 242.0, doc='AC input voltage'),
    LimitDelta('Vbus', 399.0, 11.0, doc='PFC voltage'),
    LimitLow('VbusOff', 50.0, doc='PFC voltage off'),
    LimitBetween('Vdd', 12.0, 14.0, doc='Driver_vdd internal rail'),
    LimitBetween('VsecCtl', 11.0, 15.0, doc='VsecCtl internal rail'),
    LimitBetween('VoutPre', 61.3, 78.5, doc='Output voltage before adjust'),
    LimitPercent('Vout', 70.0, 1.0, doc='Output voltage after adjust'),
    LimitLow('VoutOff', 5.0, doc='Output voltage off'),
    LimitBetween('OCP', 9.3, 13.3, doc='OCP trip limits before fine tuning'),
    LimitLow('InOCP', 9999.0,
        doc='Calculated trip voltage [Vout - (Vout * %Load Reg) / 100]'),
    LimitBoolean('Notify', True, doc='OK clicked'),
    )


class Initial(share.TestSequence):

    """SMU750-70 Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PartDetect', self._step_part_detect),
            TestStep('PowerOn', self._step_pwron),
            TestStep('AdjOutput', self._step_adj_output),
            TestStep('FullLoad', self._step_fullload),
            TestStep('OCP', self._step_ocp),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Part detect step."""
        self.measure(('dmm_lock', 'dmm_inrushoff', ), timeout=5)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power Up step."""
        dev['acsource'].output(voltage=100.0, output=True, delay=0.5)
        self.measure(
            ('dmm_vacmin', 'dmm_vdd', 'dmm_vsecctl', 'dmm_vbus',
            'dmm_voutpre'),
              timeout=5)
        dev['acsource'].output(voltage=0.0)
        dev['dcl'].output(10.0)
        time.sleep(2)
        dev['discharge'].pulse()
        mes['dmm_vbusoff'](timeout=5)
        dev['dcl'].output(0.0)

    @share.teststep
    def _step_adj_output(self, dev, mes):
        """Adjust output voltage step."""
        dev['acsource'].output(voltage=240.0, delay=0.5)
        dev['dcl'].output(0.5)
        self.measure(
            ('dmm_vac', 'dmm_vdd', 'dmm_vsecctl', 'dmm_voutpre',
            'ui_adj_vout', 'dmm_vout'),
            timeout=5)

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        dev['dcs_fixfan'].output(12.0, True)
        dev['dcl'].output(10.0)
        self.measure(
            ('dmm_vbus', 'dmm_vdd', 'dmm_vsecctl', 'dmm_vout'), timeout=5)
        dev['dcl'].output(0.5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        dev['dcl'].output(0.1)
        vout = mes['dmm_vout'](timeout=5).reading1
        trip_level = vout - (vout * VOUT_LOAD_REG) / 100
        self.limits['InOCP'].limit = trip_level
        mes['ramp_ocp'](timeout=5)
        low, high = self.limits['OCP'].limit
        dev['dcl'].output(high + 0.7)
        mes['dmm_voutoff'](timeout=10)

class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_fixfan', tester.DCSource, 'DCS3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcl'] = tester.DCLoadParallel(
            ((tester.DCLoad(self.physical_devices['DCL1']), 5),
             (tester.DCLoad(self.physical_devices['DCL5']), 5)))

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl'].output(5.0)
        time.sleep(1)
        self['discharge'].pulse()
        self['dcl'].output(0.0, False)
        self['dcs_fixfan'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['lock'] = sensor.Res(dmm, high=14, low=7, rng=10000, res=0.1)
        self['lock'].doc = 'Micro switch contacts'
        self['inrush'] = sensor.Res(dmm, high=3, low=2, rng=1000, res=0.1)
        self['inrush'].doc = 'Inrush resistors, thermal fuse, K2'
        self['vac'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['vac'].doc = 'AC input'
        self['vbus'] = sensor.Vdc(dmm, high=2, low=3, rng=1000, res=0.01)
        self['vdd'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self['vsecctl'] = sensor.Vdc(dmm, high=9, low=5, rng=100, res=0.001)
        self['vout'] = sensor.Vdc(dmm, high=11, low=4, rng=100, res=0.001)
        vout_low, vout_high = self.limits['Vout'].limit
        self['adj_vout'] = sensor.AdjustAnalog(
            sensor=self['vout'],
            low=vout_low, high=vout_high,
            message=tester.translate('smu75070_initial', 'AdjR98'),
            caption=tester.translate('smu75070_initial', 'capAdjOutput'))
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['vout'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - 0.3, stop=high + 0.3,
            step=0.25, delay=0.5)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'lock', 'Is the fixture locked?'),
            ('dmm_inrushoff', 'InrushOff', 'inrush',
                'Inrush resistors, thermal fuse and K2 in place?'),
            ('dmm_vacmin', 'VacMin', 'vac', 'AC input'),
            ('dmm_vac', 'Vac', 'vac', 'AC input'),
            ('dmm_vbus', 'Vbus', 'vbus', 'PFC output'),
            ('dmm_vbusoff', 'VbusOff', 'vbus', 'PFC output off'),
            ('dmm_vdd', 'Vdd', 'vdd', 'Driver_vdd'),
            ('dmm_vsecctl', 'VsecCtl', 'vsecctl', 'VsecCtl'),
            ('dmm_voutpre', 'VoutPre', 'vout', 'Output voltage'),
            ('dmm_vout', 'Vout', 'vout', 'Output voltage'),
            ('dmm_voutoff', 'VoutOff', 'vout', 'Output voltage off'),
            ('ui_adj_vout', 'Notify', 'adj_vout',
                'Has OK been clicked on the message box?'),
            ('ramp_ocp', 'OCP', 'ocp',
                'OCP before mounting main board in case and fine tuning CL'),
            ))