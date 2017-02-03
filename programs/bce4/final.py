#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4/5 Final Test Program."""

import time
import tester

LIMITS_4 = tester.testlimit.limitset((
    ('VoutNL', 1, 13.50, 13.80, None, None),
    ('Vout', 1, 13.28, 13.80, None, None),
    ('Vbat', 1, 13.28, 13.92, None, None),
    ('FullLoad', 1, 10.1, None, None, None),
    ('OCPramp', 1, 10.0, 13.5, None, None),
    ('inOCP', 1, 13.28, None, None, None),
    ('OCP', 1, 10.2, 13.0, None, None),
    ('AlarmOpen', 1, 9.0, 11.0, None, None),
    ('AlarmClosed', 1, 1.0, None, None, None),
    ('InDropout', 1, 13.28, None, None, None),
    ('Dropout', 1, 150.0, 180.0, None, None),
    ))

LIMITS_5 = tester.testlimit.limitset((
    ('VoutNL', 1, 27.00, 27.60, None, None),
    ('Vout', 1, 26.56, 27.84, None, None),
    ('Vbat', 1, 26.56, 27.84, None, None),
    ('FullLoad', 1, 5.1, None, None, None),
    ('OCPramp', 1, 5.0, 7.0, None, None),
    ('inOCP', 1, 26.56, None, None, None),
    ('OCP', 1, 5.1, 6.3, None, None),
    ('AlarmOpen', 1, 9.0, 11.0, None, None),
    ('AlarmClosed', 1, 1.0, None, None, None),
    ('InDropout', 1, 26.56, None, None, None),
    ('Dropout', 1, 150.0, 180.0, None, None),
    ))

LIMITS = {      # Test limit selection keyed by open() parameter
    None: LIMITS_4,
    '4': LIMITS_4,
    '5': LIMITS_5,
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """BCE4/5 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = None

    def open(self, parameter):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('LowMains', self._step_low_mains),
            )
        self._limits = LIMITS[parameter]
        self._isbce4 = (parameter != '5')
        global m, d, s, t
        d = LogicalDevices(self._devices)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        t = SubTests(d, m, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_up(self):
        """Power up unit."""
        if self._isbce4:
            self.fifo_push(
                ((s.oVout, (13.6, 13.55)), (s.oVbat, 13.3),
                 (s.oAlarm, (0.1, 10.0)), ))
        else:
            self.fifo_push(
                ((s.oVout, (27.3, 27.2)), (s.oVbat, 27.2),
                 (s.oAlarm, (0.1, 10.0)), ))
        t.power_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        if self._isbce4:
            self.fifo_push(((s.oVout, 13.4), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, 27.2), (s.oVbat, 27.1), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        if self._isbce4:
            self.fifo_push(((s.oVout, (13.4, ) * 15 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 8 + (26.0, ), ), ))
        # Load is already at FullLoad
        m.ramp_OCP.measure()

    def _step_low_mains(self):
        """Low input voltage."""
        if self._isbce4:
            self.fifo_push(((s.oVout, (13.4, ) * 17 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 17 + (26.0, ), ), ))
        t.low_mains.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_10Vfixture = tester.DCSource(devices['DCS1'])
        self.dcl_Vout = tester.DCLoad(devices['DCL1'])
        self.dcl_Vbat = tester.DCLoad(devices['DCL2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_10Vfixture.output(0.0, output=False)
        self.dcl_Vout.output(5.0, True)
        time.sleep(0.5)
        for dcl in (self.dcl_Vout, self.dcl_Vbat):
            dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oAlarm = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        ocp_start, ocp_stop = limits['OCPramp'].limit
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        self.oDropout = sensor.Ramp(
            stimulus=logical_devices.acsource, sensor=self.oVout,
            detect_limit=(limits['InDropout'], ),
            start=185.0, stop=150.0, step=-0.5, delay=0.1, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_VoutNL = Measurement(limits['VoutNL'], sense.oVout)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_AlarmOpen = Measurement(limits['AlarmOpen'], sense.oAlarm)
        self.dmm_AlarmClosed = Measurement(limits['AlarmClosed'], sense.oAlarm)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.dropout = Measurement(limits['Dropout'], sense.oDropout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements, limits):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: 185Vac, measure, 240Vac, measure.
        dc = tester.DcSubStep(((d.dcs_10Vfixture, 10.0), ))
        ld = tester.LoadSubStep(((d.dcl_Vout, 0.1), (d.dcl_Vbat, 0.0)), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_AlarmClosed, ), timeout=5)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=185.0, output=True, delay=0.5)
        msr2 = tester.MeasureSubStep((m.dmm_VoutNL, ), timeout=5)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr3 = tester.MeasureSubStep(
            (m.dmm_VoutNL, m.dmm_Vbat, m.dmm_AlarmOpen), timeout=5)
        self.power_up = tester.SubStep((dc, msr1, ld, acs1, msr2, acs2, msr3))

        # Full Load: load, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_Vout, limits['FullLoad'].limit), (d.dcl_Vbat, 0.1)))
        msr1 = tester.MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=5)
        self.full_load = tester.SubStep((ld, msr1))

        # Low Mains: 180Vac, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=185.0, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_Vout, m.dropout, ))
        self.low_mains = tester.SubStep((acs1, msr1))
