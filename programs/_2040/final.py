#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Final Test Program."""

import tester
from tester import (
    LimitLow, LimitBetween, LimitDelta
    )
import share


class Final(share.TestSequence):

    """2040 Final Test Program."""

    limitdata = (
        LimitDelta('20V', 20.0, 0.4),
        LimitBetween('20Vload', 19.4, 20.4),
        LimitLow('20Voff', 1.0),
        LimitDelta('OCP', 14.0, 2.0),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('DCPowerOn', self._step_dcpower_on),
            tester.TestStep('DCLoad', self._step_dcload),
            tester.TestStep('ACPowerOn', self._step_acpower_on),
            tester.TestStep('ACLoad', self._step_acload),
            tester.TestStep('Recover', self._step_recover),
            )

    @share.teststep
    def _step_dcpower_on(self, dev, mes):
        """Startup with DC Input, measure output at no load."""
        dev['dcs_Input'].output(10.0, output=True)
        self.measure(('dmm_20V', 'ui_YesNoGreen', ), timeout=5)
        dev['dcs_Input'].output(35.0)
        mes['dmm_20V'](timeout=5)

    @share.teststep
    def _step_dcload(self, dev, mes):
        """Measure output at full load with DC Input."""
        dev['dcl_Output'].output(2.0, output=True)
        self.measure(('dmm_20Vload', 'ui_YesNoDCOff', ), timeout=5)
        dev['dcs_Input'].output(0.0, output=False, delay=5)

    @share.teststep
    def _step_acpower_on(self, dev, mes):
        """Startup with AC Input, measure output at no load."""
        dev['dcl_Output'].output(0.0)
        dev['acsource'].output(voltage=240.0, output=True, delay=0.5)
        mes['dmm_20V'](timeout=5)

    @share.teststep
    def _step_acload(self, dev, mes):
        """Measure output at peak load with AC Input."""
        dev['dcl_Output'].output(3.5)
        self.measure(('dmm_20Vload', 'ui_YesNoACOff', ), timeout=5)
        dev['dcl_Output'].output(4.05)
        self.measure(('dmm_20Voff', 'ui_YesNoACOn', ), timeout=5)

    @share.teststep
    def _step_recover(self, dev, mes):
        """Check recovery after shutdown."""
        dev['acsource'].output(voltage=0.0, delay=0.5)
        mes['dmm_20Voff'](timeout=5)
        dev['dcl_Output'].output(0.0)
        dev['acsource'].output(voltage=240.0, delay=0.5)
        mes['dmm_20V'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ('dmm', tester.DMM, 'DMM'),
            ('acsource', tester.ACSource, 'ACS'),
            ('dcs_Input', tester.DCSource, 'DCS2'),
            ('dcl_Output', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcs_Input'].output(0.0, False)
        self['dcl_Output'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['o20V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['oYesNoGreen'] = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsPowerLedGreen?'),
            caption=tester.translate('_2040_final', 'capPowerLed'))
        self['oYesNoDCOff'] = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsDcRedLedOff?'),
            caption=tester.translate('_2040_final', 'capDcLed'))
        self['oYesNoDCOn'] = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsDcRedLedOn?'),
            caption=tester.translate('_2040_final', 'capDcLed'))
        self['oYesNoACOff'] = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsAcRedLedOff?'),
            caption=tester.translate('_2040_final', 'capAcLed'))
        self['oYesNoACOn'] = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsAcRedLedOn?'),
            caption=tester.translate('_2040_final', 'capAcLed'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_20V', '20V', 'o20V', ''),
            ('dmm_20Vload', '20Vload', 'o20V', ''),
            ('dmm_20Voff', '20Voff', 'o20V', ''),
            ('ui_YesNoGreen', 'Notify', 'oYesNoGreen', ''),
            ('ui_YesNoDCOff', 'Notify', 'oYesNoDCOff', ''),
            ('ui_YesNoDCOn', 'Notify', 'oYesNoDCOn', ''),
            ('ui_YesNoACOff', 'Notify', 'oYesNoACOff', ''),
            ('ui_YesNoACOn', 'Notify', 'oYesNoACOn', ''),
            ))
