#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3520 Final Test Program."""

import tester

LIMITS = tester.testlimit.limitset((
    ('12Voff', 1, 0.5, None, None, None),
    ('12V', 1, 13.7, 13.9, None, None),
    ('12Vfl', 13.43, 13.9, None, None, None),
    ('OCP', 1, 25.0, 30.3, None, None),
    ('inOCP', 1, 13.3, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """TS3520 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('FuseCheck', self._step_fuse_check),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Poweroff', self._step_power_off),
            )
        self._limits = LIMITS
        global m, d, s, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d, self._limits)
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

    def _step_fuse_check(self):
        """Powerup with output fuse removed, measure output off.

        Check Mains light and Red led.

        """
        self.fifo_push(
            ((s.oNotifyStart, True), (s.o12V_1, 0.0),
             (s.oYesNoRed, True), (s.oNotifyFuse, True), ))
        t.fuse_check.run()

    def _step_power_up(self):
        """Switch on unit at 240Vac, measure output voltages at no load."""
        self.fifo_push(
            ((s.o12V_1, 13.8), (s.o12V_2, 13.8), (s.o12V_3, 13.8),
             (s.oYesNoGreen, True), ))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.o12V_1, 13.6), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o12V_1, (13.4, ) * 15 + (13.0, ), ), ))
        m.ramp_OCP.measure()

    def _step_power_off(self):
        """Switch off unit, measure output voltage."""
        self.fifo_push(
            ((s.oNotifyMains, True), (s.o12V_1, 0.0), (s.oYesNoOff, True), ))
        t.pwr_off.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        _dcl_12Va = tester.DCLoad(devices['DCL1'])
        _dcl_12Vb = tester.DCLoad(devices['DCL2'])
        self.dcl = tester.DCLoadParallel(
            ((_dcl_12Va, 12.5), (_dcl_12Vb, 12.5)))

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.o12V_1 = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12V_2 = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12V_3 = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.oNotifyStart = sensor.Notify(
            message=tester.translate('ts3520_final', 'RemoveFuseSwitchOn'),
            caption=tester.translate('ts3520_final', 'capSwitchOn'))
        self.oNotifyFuse = sensor.Notify(
            message=tester.translate('ts3520_final', 'ReplaceFuse'),
            caption=tester.translate('ts3520_final', 'capReplaceFuse'))
        self.oNotifyMains = sensor.Notify(
            message=tester.translate('ts3520_final', 'SwitchOff'),
            caption=tester.translate('ts3520_final', 'capSwitchOff'))
        self.oYesNoRed = sensor.YesNo(
            message=tester.translate('ts3520_final', 'IsRedLedOn?'),
            caption=tester.translate('ts3520_final', 'capRedLed'))
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('ts3520_final', 'IsGreenLedOn?'),
            caption=tester.translate('ts3520_final', 'capGreenLed'))
        self.oYesNoOff = sensor.YesNo(
            message=tester.translate('ts3520_final', 'AreAllLightsOff?'),
            caption=tester.translate('ts3520_final', 'capAllOff'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.o12V_1,
            detect_limit=(limits['inOCP'], ),
            start=24.5, stop=31.0, step=0.1, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V_1)
        self.dmm_12V_1 = Measurement(limits['12V'], sense.o12V_1)
        self.dmm_12V_2 = Measurement(limits['12V'], sense.o12V_2)
        self.dmm_12V_3 = Measurement(limits['12V'], sense.o12V_3)
        self.dmm_12Vfl = Measurement(limits['12Vfl'], sense.o12V_1)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ui_NotifyStart = Measurement(limits['Notify'], sense.oNotifyStart)
        self.ui_NotifyFuse = Measurement(limits['Notify'], sense.oNotifyFuse)
        self.ui_NotifyMains = Measurement(limits['Notify'], sense.oNotifyMains)
        self.ui_YesNoRed = Measurement(limits['Notify'], sense.oYesNoRed)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoOff = Measurement(limits['Notify'], sense.oYesNoOff)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # OutputFuseCheck: Remove output fuse, Mains on, measure, restore fuse.
        msr1 = tester.MeasureSubStep((m.ui_NotifyStart, ))
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr2 = tester.MeasureSubStep((m.dmm_12Voff, m.ui_YesNoRed), timeout=5)
        acs2 = tester.AcSubStep(
            acs=d.acsource, voltage=0.0, output=True, delay=0.5)
        msr3 = tester.MeasureSubStep((m.ui_NotifyFuse, ))
        self.fuse_check = tester.SubStep((msr1, acs1, msr2, acs2, msr3))
        # PowerUp: Apply 240Vac, measure.
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = tester.MeasureSubStep(
            (m.dmm_12V_1, m.dmm_12V_2, m.dmm_12V_3,
             m.ui_YesNoGreen), timeout=5)
        self.pwr_up = tester.SubStep((acs, msr))
        # FullLoad: Full load, measure.
        ld = tester.LoadSubStep(((d.dcl, 25.0),), output=True)
        msr = tester.MeasureSubStep((m.dmm_12Vfl, ), timeout=5)
        self.full_load = tester.SubStep((ld, msr))
        # PowerOff: Switch mains off, measure.
        acs = tester.AcSubStep(acs=d.acsource, voltage=0.0, delay=0.5)
        msr = tester.MeasureSubStep(
            (m.ui_NotifyMains, m.dmm_12Voff, m.ui_YesNoOff), timeout=5)
        self.pwr_off = tester.SubStep((acs, msr))
