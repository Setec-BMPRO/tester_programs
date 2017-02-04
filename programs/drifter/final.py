#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

import tester
from tester.testlimit import lim_hilo_delta, lim_lo, lim_hi, lim_boolean

LIMITS = tester.testlimit.limitset((
    lim_lo('SwOff', 1.0),
    lim_hi('SwOn', 10.0),
    lim_hilo_delta('USB5V', 5.00, 0.25),
    lim_boolean('Notify', True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """Drifter Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('DisplayCheck', self._step_displ_check),
            tester.TestStep('SwitchCheck', self._step_sw_check),
            )
        self._limits = LIMITS
        global m, d, s, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_displ_check(self):
        """Apply DC Input voltage and check the display."""
        self.fifo_push(
            ((s.oYesNoSeg, True), (s.oYesNoBklight, True),
             (s.oYesNoDisplay, True), ))

        t.displ_check.run()

    def _step_sw_check(self):
        """Check the operation of the rocker switches, check USB 5V."""
        self.fifo_push(
            ((s.oNotifySwOff, True), (s.oWaterPump, 0.1), (s.oBattSw, 0.1),
             (s.oNotifySwOn, True), (s.oWaterPump, 11.0), (s.oBattSw, 11.0),
             (s.oUSB5V, 5.0), ))

        tester.MeasureGroup(
            (m.ui_NotifySwOff, m.dmm_PumpOff, m.dmm_BattDisconn,
             m.ui_NotifySwOn, m.dmm_PumpOn, m.dmm_BattConnect, m.dmm_USB5V),
            timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Isense = tester.DCSource(devices['DCS1'])
        self.dcs_12V = tester.DCSource(devices['DCS2'])
        self.dcs_Level = tester.DCSource(devices['DCS3'])

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_Isense, self.dcs_12V, self.dcs_Level):
            dcs.output(0.0, output=False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oWaterPump = sensor.Vdc(dmm, high=1, low=2, rng=100, res=0.1)
        self.oBattSw = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self.oUSB5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oYesNoSeg = sensor.YesNo(
            message=tester.translate('drifter_final', 'AreSegmentsOn?'),
            caption=tester.translate('drifter_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsBacklightOk?'),
            caption=tester.translate('drifter_final', 'capBacklight'))
        self.oYesNoDisplay = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsDisplayOk?'),
            caption=tester.translate('drifter_final', 'capDisplay'))
        self.oNotifySwOff = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOff'),
            caption=tester.translate('drifter_final', 'capSwitchOff'))
        self.oNotifySwOn = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOn'),
            caption=tester.translate('drifter_final', 'capSwitchOn'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_PumpOff = Measurement(
            limits['SwOff'], sense.oWaterPump)
        self.dmm_PumpOn = Measurement(
            limits['SwOn'], sense.oWaterPump)
        self.dmm_BattDisconn = Measurement(
            limits['SwOff'], sense.oBattSw)
        self.dmm_BattConnect = Measurement(
            limits['SwOn'], sense.oBattSw)
        self.dmm_USB5V = Measurement(
            limits['USB5V'], sense.oUSB5V)
        self.ui_YesNoSeg = Measurement(
            limits['Notify'], sense.oYesNoSeg)
        self.ui_YesNoBklight = Measurement(
            limits['Notify'], sense.oYesNoBklight)
        self.ui_YesNoDisplay = Measurement(
            limits['Notify'], sense.oYesNoDisplay)
        self.ui_NotifySwOff = Measurement(
            limits['Notify'], sense.oNotifySwOff)
        self.ui_NotifySwOn = Measurement(
            limits['Notify'], sense.oNotifySwOn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # DisplayCheck: Apply power, check display.
        self.displ_check = tester.SubStep((
            tester.DcSubStep(
                setting=((d.dcs_Isense, 0.2), ), output=True, delay=0.5),
            tester.DcSubStep(
                setting=((d.dcs_12V, 12.0), ), output=True, delay=5),
            tester.MeasureSubStep(
                (m.ui_YesNoSeg, m.ui_YesNoBklight, )),
            tester.DcSubStep(
                setting=((d.dcs_Isense, 0.0), (d.dcs_12V, 0.0), ),
                output=False, delay=1),
            tester.DcSubStep(
                setting=((d.dcs_12V, 12.0), ), output=True, delay=5),
            tester.MeasureSubStep((m.ui_YesNoDisplay, )),
            ))
