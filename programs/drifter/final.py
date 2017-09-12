#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

import tester
from tester import TestStep, LimitLow, LimitHigh, LimitDelta
import share


class Final(share.TestSequence):

    """Drifter Final Test Program."""

    limitdata = (
        LimitLow('SwOff', 1.0),
        LimitHigh('SwOn', 10.0),
        LimitDelta('USB5V', 5.00, 0.25),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('DisplayCheck', self._step_displ_check),
            TestStep('SwitchCheck', self._step_sw_check),
            )

    @share.teststep
    def _step_displ_check(self, dev, mes):
        """Apply DC Input voltage and check the display."""
        dev['dcs_Isense'].output(0.2, output=True, delay=0.5)
        dev['dcs_12V'].output(12.0, output=True, delay=5)
        self.measure(('ui_YesNoSeg', 'ui_YesNoBklight', ))
        self.dcsource(
            (('dcs_Isense', 0.0), ('dcs_12V', 0.0), ),
            output=False, delay=1)
        dev['dcs_12V'].output(12.0, output=True, delay=5)
        mes['ui_YesNoDisplay']()

    @share.teststep
    def _step_sw_check(self, dev, mes):
        """Check the operation of the rocker switches, check USB 5V."""
        self.measure(
            ('ui_NotifySwOff', 'dmm_PumpOff', 'dmm_BattDisconn',
             'ui_NotifySwOn', 'dmm_PumpOn', 'dmm_BattConnect', 'dmm_USB5V'),
            timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ('dmm', tester.DMM, 'DMM'),
            ('dcs_12V', tester.DCSource, 'DCS2'),
            ('dcs_Level', tester.DCSource, 'DCS3'),
            ('dcs_Isense', tester.DCSource, 'DCS4'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_Isense', 'dcs_12V', 'dcs_Level'):
            self[dcs].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oWaterPump'] = sensor.Vdc(dmm, high=1, low=2, rng=100, res=0.1)
        self['oBattSw'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self['oUSB5V'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self['oYesNoSeg'] = sensor.YesNo(
            message=tester.translate('drifter_final', 'AreSegmentsOn?'),
            caption=tester.translate('drifter_final', 'capSegments'))
        self['oYesNoBklight'] = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsBacklightOk?'),
            caption=tester.translate('drifter_final', 'capBacklight'))
        self['oYesNoDisplay'] = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsDisplayOk?'),
            caption=tester.translate('drifter_final', 'capDisplay'))
        self['oNotifySwOff'] = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOff'),
            caption=tester.translate('drifter_final', 'capSwitchOff'))
        self['oNotifySwOn'] = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOn'),
            caption=tester.translate('drifter_final', 'capSwitchOn'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_PumpOff', 'SwOff', 'oWaterPump', ''),
            ('dmm_PumpOn', 'SwOn', 'oWaterPump', ''),
            ('dmm_BattDisconn', 'SwOff', 'oBattSw', ''),
            ('dmm_BattConnect', 'SwOn', 'oBattSw', ''),
            ('dmm_USB5V', 'USB5V', 'oUSB5V', ''),
            ('ui_YesNoSeg', 'Notify', 'oYesNoSeg', ''),
            ('ui_YesNoBklight', 'Notify', 'oYesNoBklight', ''),
            ('ui_YesNoDisplay', 'Notify', 'oYesNoDisplay', ''),
            ('ui_NotifySwOff', 'Notify', 'oNotifySwOff', ''),
            ('ui_NotifySwOn', 'Notify', 'oNotifySwOn', ''),
        ))
