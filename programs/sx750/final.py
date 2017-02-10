#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Final Test Program."""

import tester
from tester import (
    TestStep,
    LimitLo, LimitBoolean, LimitHiLo, LimitHiLoDelta
    )
import share

LIMITS = (
    LimitHiLoDelta('InRes', (70000, 10000)),
    LimitLo('IECoff', 0.5),
    LimitHiLoDelta('IEC', (240, 5)),
    LimitHiLo('5V', (5.034, 5.177)),
    LimitLo('12Voff', 0.5),
    LimitHiLo('12Von', (12.005, 12.495)),
    LimitHiLo('24Von', (23.647, 24.613)),
    LimitHiLo('5Vfl', (4.820, 5.380)),
    LimitHiLo('12Vfl', (11.270, 13.230)),
    LimitHiLo('24Vfl', (21.596, 26.663)),
    LimitLo('PwrGood', 0.5),
    LimitHiLoDelta('AcFail', (5.0, 0.5)),
    LimitHiLo('Reg12V', (0.5, 5.0)),
    LimitHiLo('Reg24V', (0.2, 5.0)),
    LimitBoolean('Notify', True),
    )


class Final(share.TestSequence):

    """SX-750 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('InputRes', self._step_inres),
            TestStep('PowerUp', self._step_powerup),
            TestStep('PowerOn', self._step_poweron),
            TestStep('Load', self._step_load),
            )

    @share.teststep
    def _step_inres(self, dev, mes):
        """Verify that the hand loaded input discharge resistors are there."""
        mes['dmm_InpRes'](timeout=5)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Switch on unit at 240Vac, light load, not enabled."""
        self.dcload(
            (('dcl_5v', 0.0), ('dcl_12v', 0.1), ('dcl_24v', 0.1)),
            output=True)
        mes['dmm_Iecoff'](timeout=5)
        dev['acsource'].output(240.0, output=True, delay=0.5)
        self.measure(
            ('dmm_Iec', 'dmm_5v', 'dmm_12voff', 'ui_YesNoGreen'),
            timeout=5)

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Enable all outputs and check that the LED goes blue."""
        dev['rla_PwrOn'].set_on()
        self.measure(
            ('ui_YesNoBlue', 'dmm_5v', 'dmm_PwrGood', 'dmm_AcFail', ),
            timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure loaded outputs and load regulation."""
        nl12v, nl24v = self.measure(('dmm_12von', 'dmm_24von', )).readings
        self.dcload(
            (('dcl_5v', 2.0), ('dcl_12v', 32.0), ('dcl_24v', 15.0)),
            output=True)
        self.measure(('dmm_5vfl', 'dmm_PwrGood', 'dmm_AcFail', ), timeout=2)
        fl12v, fl24v = self.measure(('dmm_12vfl', 'dmm_24vfl', )).readings
        if self.running:
            # Load regulation values in %
            mes['reg12v'].sensor.store(100 * (nl12v - fl12v) / nl12v)
            mes['reg24v'].sensor.store(100 * (nl24v - fl24v) / nl24v)
            self.measure(('reg12v', 'reg24v', ))


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_12v', tester.DCLoad, 'DCL1'),
                ('dcl_24v', tester.DCLoad, 'DCL2'),
                ('dcl_5v', tester.DCLoad, 'DCL3'),
                ('rla_PwrOn', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].output(voltage=0.0, output=False)
        self['dcl_12v'].output(10, delay=0.5)
        for load in ('dcl_12v', 'dcl_24v', 'dcl_5v'):
            self[load].output(0.0, False)
        self['rla_PwrOn'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oInpRes'] = sensor.Res(dmm, high=1, low=1, rng=1000000, res=1)
        self['oIec'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['o5v'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self['o12v'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['o24v'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['oPwrGood'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self['oAcFail'] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self['oMir12v'] = sensor.Mirror()
        self['oMir24v'] = sensor.Mirror()
        self['oYesNoGreen'] = sensor.YesNo(
            message=tester.translate('sx750_final', 'IsLedGreen?'),
            caption=tester.translate('sx750_final', 'capLedGreen'))
        self['oYesNoBlue'] = sensor.YesNo(
            message=tester.translate('sx750_final', 'IsLedBlue?'),
            caption=tester.translate('sx750_final', 'capLedBlue'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        for measurement_name, limit_name, sensor_name in (
                ('reg12v', 'Reg12V', 'oMir12v'),
                ('reg24v', 'Reg24V', 'oMir24v'),
                ('dmm_InpRes', 'InRes', 'oInpRes'),
                ('dmm_Iecoff', 'IECoff', 'oIec'),
                ('dmm_Iec', 'IEC', 'oIec'),
                ('dmm_5v', '5V', 'o5v'),
                ('dmm_12voff', '12Voff', 'o12v'),
                ('dmm_12von', '12Von', 'o12v'),
                ('dmm_24von', '24Von', 'o24v'),
                ('dmm_PwrGood', 'PwrGood', 'oPwrGood'),
                ('dmm_AcFail', 'AcFail', 'oAcFail'),
                ('dmm_5vfl', '5Vfl', 'o5v'),
                ('dmm_12vfl', '12Vfl', 'o12v'),
                ('dmm_24vfl', '24Vfl', 'o24v'),
                ('ui_YesNoGreen', 'Notify', 'oYesNoGreen'),
                ('ui_YesNoBlue', 'Notify', 'oYesNoBlue'),
            ):
            self[measurement_name] = tester.Measurement(
                self.limits[limit_name], self.sensors[sensor_name])
