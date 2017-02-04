#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ATXG-450-2V Final Test Program."""

import tester

LIMITS = tester.testlimit.limitset((
    ('5Vsb', 1, 4.845, 5.202, None, None),
    ('5Vsbinocp', 1, 4.70, None, None, None),
    ('5Vsbocp', 1, 2.6, 4.0, None, None),
    ('24Voff', 1, 0.5, None, None, None),
    ('24Von', 1, 23.75, 26.25, None, None),
    ('24Vinocp', 1, 22.8, None, None, None),
    ('24Vocp', 1, 18.0, 24.0, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 11.685, 12.669, None, None),
    ('12Vinocp', 1, 10.0, None, None, None),
    ('12Vocp', 1, 20.5, 26.0, None, None),
    ('5Voff', 1, 0.5, None, None, None),
    ('5Von', 1, 4.725, 5.4075, None, None),
    ('5Vinocp', 1, 4.75, None, None, None),
    ('5Vocp', 1, 20.5, 26.0, None, None),
    ('3V3off', 1, 0.5, None, None, None),
    ('3V3on', 1, 3.1825, 3.4505, None, None),
    ('3V3inocp', 1, 3.20, None, None, None),
    ('3V3ocp', 1, 17.0, 26.0, None, None),
    ('-12Voff', 1, None, -0.5, None, None),
    ('-12Von', 1, -12.48, -11.52, None, None),
    ('PwrGoodOff', 1, 0.5, None, None, None),
    ('PwrGoodOn', 1, None, 4.5, None, None),
    ('PwrFailOff', 1, None, 4.5, None, None),
    ('PwrFailOn', 1, 0.5, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final2V(tester.TestSequence):

    """ATXG-450-2V Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('SwitchOn', self._step_switch_on),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerFail', self._step_power_fail),
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

    def _step_power_up(self):
        """Switch on unit at 240Vac, not enabled, measure output voltages."""
        self.fifo_push(
            ((s.o5Vsb, 5.10), (s.oYesNoGreen, True), (s.o24V, 0.0),
             (s.o12V, 0.0), (s.o5V, 0.0), (s.o3V3, 0.0), (s.on12V, 0.0),
             (s.oPwrGood, 0.1), (s.oPwrFail, 5.0)))
        t.pwr_up.run()

    def _step_switch_on(self):
        """Enable outputs, measure."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o12V, 12.0), (s.o5V, 5.0), (s.o3V3, 3.3),
             (s.on12V, -12.0), (s.oPwrGood, 5.0), (s.oPwrFail, 0.1),
             (s.oYesNoFan, True)))
        t.sw_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o12V, 12.0), (s.o5V, 5.0), (s.o3V3, 3.3),
             (s.on12V, -12.0), (s.oPwrGood, 5.0), (s.oPwrFail, 0.1)))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP points."""
        # drop back to minimum loads
        for dcl, current in (
                (d.dcl_5Vsb, 0.0), (d.dcl_24V, 0.5), (d.dcl_12V, 0.5),
                (d.dcl_5V, 0.5), (d.dcl_3V3, 0.0)):
            dcl.output(current)
        # 24V OCP
        self.fifo_push(((s.o24V, (24.1, ) * 15 + (22.0, ), ), ))
        d.dcl_24V.binary(0.0, 17.5, 5.0)
        m.ramp_24Vocp.measure()
        d.dcl_24V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 12V OCP
        self.fifo_push(((s.o12V, (12.1, ) * 15 + (11.0, ), ), ))
        d.dcl_12V.binary(0.0, 19.5, 1.0)
        m.ramp_12Vocp.measure()
        d.dcl_12V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 5V OCP
        self.fifo_push(((s.o5V, (5.1, ) * 15 + (4.0, ), ), ))
        d.dcl_5V.binary(0.0, 19.5, 1.0)
        m.ramp_5Vocp.measure()
        d.dcl_5V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 3V3 OCP
        self.fifo_push(((s.o3V3, (3.3, ) * 15 + (3.0, ), ), ))
        d.dcl_3V3.binary(0.0, 16.5, 5.0)
        m.ramp_3V3ocp.measure()
        d.dcl_3V3.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 5Vsb OCP
        self.fifo_push(((s.o5Vsb, (5.1, ) * 10 + (4.0, ), ), ))
        d.dcl_5Vsb.binary(0.0, 2.1, 1.0)
        m.ramp_5Vsbocp.measure()
        d.dcl_5Vsb.output(0.0)
        t.restart.run()

    def _step_power_fail(self):
        """Switch off unit, measure."""
        self.fifo_push(((s.oPwrFail, 5.05), ))
        t.pwr_fail.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        # This DC Source controls the PS_ON signal (12V == Unit OFF)
        self.dcs_PsOn = tester.DCSource(devices['DCS1'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])
        self.dcl_12V = tester.DCLoad(devices['DCL2'])
        self.dcl_5V = tester.DCLoad(devices['DCL3'])
        self.dcl_3V3 = tester.DCLoad(devices['DCL4'])
        self.dcl_5Vsb = tester.DCLoad(devices['DCL5'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for ld in (self.dcl_24V, self.dcl_12V, self.dcl_5V,
                   self.dcl_3V3, self.dcl_5Vsb):
            ld.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oIec = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.o5Vsb = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.0001)
        self.on12V = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oPwrGood = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.oPwrFail = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('atxg450_2v_final', 'IsSwitchGreen?'),
            caption=tester.translate('atxg450_2v_final', 'capSwitchGreen'))
        self.oYesNoFan = sensor.YesNo(
            message=tester.translate('atxg450_2v_final', 'IsFanRunning?'),
            caption=tester.translate('atxg450_2v_final', 'capFan'))
        self.o24Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_24V, sensor=self.o24V,
            detect_limit=(limits['24Vinocp'], ),
            start=17.5, stop=24.5, step=0.1, delay=0.1)
        self.o12Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_12V, sensor=self.o12V,
            detect_limit=(limits['12Vinocp'], ),
            start=19.5, stop=26.5, step=0.1, delay=0.1)
        self.o5Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_5V, sensor=self.o5V,
            detect_limit=(limits['5Vinocp'], ),
            start=19.5, stop=26.5, step=0.1, delay=0.1)
        self.o3V3ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_3V3, sensor=self.o3V3,
            detect_limit=(limits['3V3inocp'], ),
            start=16.5, stop=26.5, step=0.1, delay=0.1)
        self.o5Vsbocp = sensor.Ramp(
            stimulus=logical_devices.dcl_5Vsb, sensor=self.o5Vsb,
            detect_limit=(limits['5Vsbinocp'], ),
            start=2.1, stop=4.7, step=0.1, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_5Vsb = Measurement(limits['5Vsb'], sense.o5Vsb)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V)
        self.dmm_5Voff = Measurement(limits['5Voff'], sense.o5V)
        self.dmm_3V3off = Measurement(limits['3V3off'], sense.o3V3)
        self.dmm_n12Voff = Measurement(limits['-12Voff'], sense.on12V)
        self.dmm_24Von = Measurement(limits['24Von'], sense.o24V)
        self.dmm_12Von = Measurement(limits['12Von'], sense.o12V)
        self.dmm_5Von = Measurement(limits['5Von'], sense.o5V)
        self.dmm_3V3on = Measurement(limits['3V3on'], sense.o3V3)
        self.dmm_n12Von = Measurement(limits['-12Von'], sense.on12V)
        self.dmm_PwrFailOff = Measurement(limits['PwrFailOff'], sense.oPwrFail)
        self.dmm_PwrGoodOff = Measurement(limits['PwrGoodOff'], sense.oPwrGood)
        self.dmm_PwrFailOn = Measurement(limits['PwrFailOn'], sense.oPwrFail)
        self.dmm_PwrGoodOn = Measurement(limits['PwrGoodOn'], sense.oPwrGood)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)
        self.ramp_24Vocp = Measurement(limits['24Vocp'], sense.o24Vocp)
        self.ramp_12Vocp = Measurement(limits['12Vocp'], sense.o12Vocp)
        self.ramp_5Vocp = Measurement(limits['5Vocp'], sense.o5Vocp)
        self.ramp_3V3ocp = Measurement(limits['3V3ocp'], sense.o3V3ocp)
        self.ramp_5Vsbocp = Measurement(limits['5Vsbocp'], sense.o5Vsbocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: Disable PS_ON, apply 240Vac, measure.
        dcs = tester.DcSubStep(((d.dcs_PsOn, 12.0), ), output=True, delay=0.1)
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = tester.MeasureSubStep(
            (m.dmm_5Vsb, m.ui_YesNoGreen, m.dmm_24Voff, m.dmm_12Voff,
             m.dmm_5Voff, m.dmm_3V3off, m.dmm_n12Voff, m.dmm_PwrGoodOff,
             m.dmm_PwrFailOff), timeout=5)
        self.pwr_up = tester.SubStep((dcs, acs, msr))

        # SwitchOn: Min load, enable PS_ON, measure.
        ld = tester.LoadSubStep(((d.dcl_12V, 1.0), (d.dcl_24V, 1.0), (d.dcl_5V, 1.0)))
        dcs = tester.DcSubStep(((d.dcs_PsOn, 0.0), ), output=True, delay=0.1)
        msr = tester.MeasureSubStep(
            (m.dmm_24Von, m.dmm_12Von, m.dmm_5Von, m.dmm_3V3on, m.dmm_n12Von,
             m.dmm_PwrGoodOn, m.dmm_PwrFailOn, m.ui_YesNoFan), timeout=5)
        self.sw_on = tester.SubStep((ld, dcs, msr))

        # Full Load: Apply full load, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_5Vsb, 1.0), (d.dcl_24V, 5.0), (d.dcl_5V, 10.0),
             (d.dcl_12V, 10.0), (d.dcl_3V3, 10.0)), delay=0.5)
        msr = tester.MeasureSubStep(
            (m.dmm_5Vsb, m.dmm_24Von, m.dmm_12Von, m.dmm_5Von, m.dmm_3V3on,
             m.dmm_n12Von, m.dmm_PwrGoodOn, m.dmm_PwrFailOn), timeout=5)
        self.full_load = tester.SubStep((ld, msr))

        # PowerFail: Switch AC off, measure.
        acs = tester.AcSubStep(acs=d.acsource, voltage=0.0, output=False, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_PwrFailOff, ))
        self.pwr_fail = tester.SubStep((acs, msr1,))

        # Re-Start unit after OCP by using PS_ON.
        dcs1 = tester.DcSubStep(((d.dcs_PsOn, 12.0), ), output=True, delay=0.5)
        dcs2 = tester.DcSubStep(((d.dcs_PsOn, 0.0), ), output=True, delay=2.0)
        self.restart = tester.SubStep((dcs1, dcs2,))
