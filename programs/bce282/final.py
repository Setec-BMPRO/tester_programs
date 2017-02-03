#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Final Program."""

# FIXME: This program is not finished yet!

import time
import tester

LIMITS_12 = tester.testlimit.limitset((
    ('VoutST', 1, 6.0, 14.0, None, None),
    ('VoutNL', 1, 13.35, 13.75, None, None),
    ('VbatNL', 1, 13.20, 13.75, None, None),
    ('Vout', 1, 12.98, 13.75, None, None),
    ('Vbat', 1, 12.98, 13.75, None, None),
    ('FullLoad', 1, 20.1, None, None, None),
    ('OCPrampLoad', 1, 20.0, 25.5, None, None),
    ('OCPrampBatt', 1, 10.0, 12.5, None, None),
    ('inOCP', 1, 12.98, None, None, None),
    ('OCPLoad', 1, 20.0, 25.0, None, None),
    ('OCPBatt', 1, 10.0, 12.0, None, None),
    ('AlarmOpen', 1, 9000, 11000, None, None),
    ('AlarmClosed', 1, 100, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

LIMITS_24 = tester.testlimit.limitset((
    ('VoutST', 1, 12.0, 28.0, None, None),
    ('VoutNL', 1, 27.35, 27.85, None, None),
    ('VbatNL', 1, 27.35, 27.85, None, None),
    ('Vout', 1, 26.80, 27.85, None, None),
    ('Vbat', 1, 26.80, 27.85, None, None),
    ('FullLoad', 1, 10.1, None, None, None),
    ('OCPrampLoad', 1, 10.0, 13.5, None, None),
    ('OCPrampBatt', 1, 5.0, 6.5, None, None),
    ('inOCP', 1, 26.80, None, None, None),
    ('OCPLoad', 1, 10.0, 13.0, None, None),
    ('OCPBatt', 1, 5.0, 6.0, None, None),
    ('AlarmOpen', 1, 9000, 11000, None, None),
    ('AlarmClosed', 1, 100, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

LIMITS = {      # Test limit selection keyed by open() parameter
    None: LIMITS_12,
    '12': LIMITS_12,
    '24': LIMITS_24
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """BCE282-12/24 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = None

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            )
        super().open(sequence)
        self._limits = LIMITS[parameter]
        self._isbce12 = (parameter != '24')
        global d, s, m, t
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
        self.fifo_push(((s.oAlarm, (1, 10000)), ))
        if self._isbce12:
            self.fifo_push(((s.oVout, (13.6, 13.55)), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, (27.6, 27.6)), (s.oVbat, 27.5), ))
        t.power_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.oYesNoGreen, True), ))
        if self._isbce12:
            self.fifo_push(((s.oVout, 13.4), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, 27.2), (s.oVbat, 27.1), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        if self._isbce12:
            self.fifo_push(((s.oVout, (13.4, ) * 15 + (13.0, ), ),
                            (s.oVbat, (13.4, ) * 15 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 8 + (26.0, ), ),
                            (s.oVbat, (27.3, ) * 8 + (26.0, ), ), ))
        m.ramp_OCPLoad.measure()
        d.dcl_Vout.output(0.0)
        m.ramp_OCPBatt.measure()
        d.dcl_Vbat.output(0.0)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_Vout = tester.DCLoad(devices['DCL1'])
        self.dcl_Vbat = tester.DCLoad(devices['DCL2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_Vout.output(10.0, True)
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
        self.oAlarm = sensor.Res(dmm, high=5, low=3, rng=100000, res=1)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('bce282_final', 'IsGreenFlash?'),
            caption=tester.translate('bce282_final', 'capLedGreen'))
        ocp_start, ocp_stop = limits['OCPrampLoad'].limit
        self.oOCPLoad = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        ocp_start, ocp_stop = limits['OCPrampBatt'].limit
        self.oOCPBatt = sensor.Ramp(
            stimulus=logical_devices.dcl_Vbat, sensor=self.oVbat,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_VoutNL = Measurement(limits['VoutNL'], sense.oVout)
        self.dmm_VbatNL = Measurement(limits['VbatNL'], sense.oVbat)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_AlarmClosed = Measurement(limits['AlarmClosed'], sense.oAlarm)
        self.dmm_AlarmOpen = Measurement(limits['AlarmOpen'], sense.oAlarm)
        self.ramp_OCPLoad = Measurement(limits['OCPLoad'], sense.oOCPLoad)
        self.ramp_OCPBatt = Measurement(limits['OCPBatt'], sense.oOCPBatt)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements, limits):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 200Vac, measure, 240Vac, measure.
        msr1 = tester.MeasureSubStep((m.dmm_AlarmClosed, ), timeout=5)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=200.0, output=True, delay=0.5)
        ld = tester.LoadSubStep(((d.dcl_Vout, 0.1), (d.dcl_Vbat, 0.0)), output=True)
        msr2 = tester.MeasureSubStep((m.dmm_VoutNL, ), timeout=5)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr3 = tester.MeasureSubStep(
            (m.dmm_VoutNL, m.dmm_VbatNL, m.dmm_AlarmOpen), timeout=5)
        self.power_up = tester.SubStep((msr1, acs1, ld, msr2, acs2, msr3))
        # Full Load: load, measure.
        ld1 = tester.LoadSubStep(((d.dcl_Vbat, 0.5), ))
        msr1 = tester.MeasureSubStep((m.ui_YesNoGreen, ), timeout=5)
        ld2 = tester.LoadSubStep(
            ((d.dcl_Vbat, 0.0), (d.dcl_Vout, limits['FullLoad'].limit)))
        msr2 = tester.MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=5)
        self.full_load = tester.SubStep((ld1, msr1, ld2, msr2))
