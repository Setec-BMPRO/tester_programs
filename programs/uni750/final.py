#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNI-750 Final Test Program."""

import tester

LIMITS = tester.testlimit.limitset((
    ('AcUnsw', 1, 235, 245, None, None),
    ('AcSwOff', 1, 0.5, None, None, None),
    ('AcSwOn', 1, 235, 245, None, None),
    ('24V', 1, 23.256, 24.552, None, None),
    ('24Vfl', 1, 23.5, 24.3, None, None),
    ('15V', 1, 14.25, 15.75, None, None),
    ('12V', 1, 11.4, 12.6, None, None),
    ('5V', 1, 5.0, 5.212, None, None),
    ('3.3V', 1, 3.25, 3.423, None, None),
    ('5Vi', 1, 4.85, 5.20, None, None),
    ('PGood', 1, 5.0, 5.25, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """UNI-750 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('FullLoad', self._step_full_load),
            )
        super().open(sequence)
        global m, d, s, t
        d = LogicalDevices(self._devices)
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

    def _step_power_up(self):
        """Connect unit to 240Vac, Remote AC Switch off."""
        self.fifo_push(((s.oAcUnsw, 240.0), (s.oAcSw, 0.0), ))
        t.pwr_up.run()

    def _step_power_on(self):
        """Remote AC Switch on, measure outputs at min load."""
        self.fifo_push(
            ((s.oAcSw, 240.0), (s.oYesNoFan, True), (s.o24V, 24.5),
             (s.o15V, 15.0), (s.o12V, 12.0), (s.o5V, 5.1),
             (s.o3V3, 3.3), (s.o5Vi, 5.2), (s.oPGood, 5.2), ))
        t.pwr_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o15V, 15.0), (s.o12V, 12.0),
             (s.o5V, 5.1), (s.o3V3, 3.3), (s.o5Vi, 5.15),
             (s.oPGood, 5.2), ))
        t.full_load.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        # This DC Source drives the Remote AC Switch
        self.dcs_PwrOn = tester.DCSource(devices['DCS1'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])
        self.dcl_15V = tester.DCLoad(devices['DCL2'])
        self.dcl_12V = tester.DCLoad(devices['DCL3'])
        self.dcl_5V = tester.DCLoad(devices['DCL4'])
        self.dcl_3V3 = tester.DCLoad(devices['DCL5'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_PwrOn.output(0.0, output=False)
        for ld in (self.dcl_24V, self.dcl_15V, self.dcl_12V,
                   self.dcl_5V, self.dcl_3V3):
            ld.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oAcUnsw = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.oAcSw = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.1)
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.001)
        self.o5Vi = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self.oPGood = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.01)
        self.oYesNoFan = sensor.YesNo(
            message=tester.translate('uni750_final', 'IsFanOn?'),
            caption=tester.translate('uni750_final', 'capFan'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_AcUnsw = Measurement(limits['AcUnsw'], sense.oAcUnsw)
        self.dmm_AcSwOff = Measurement(limits['AcSwOff'], sense.oAcSw)
        self.dmm_AcSwOn = Measurement(limits['AcSwOn'], sense.oAcSw)
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_24Vfl = Measurement(limits['24Vfl'], sense.o24V)
        self.dmm_15V = Measurement(limits['15V'], sense.o15V)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_3V3 = Measurement(limits['3.3V'], sense.o3V3)
        self.dmm_5Vi = Measurement(limits['5Vi'], sense.o5Vi)
        self.dmm_PGood = Measurement(limits['PGood'], sense.oPGood)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, measure.
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = tester.MeasureSubStep((m.dmm_AcUnsw, m.dmm_AcSwOff, ), timeout=5)
        self.pwr_up = tester.SubStep((acs, msr))
        # PowerOn: Set min load, switch on, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_24V, 3.0), (d.dcl_15V, 1.0), (d.dcl_12V, 2.0),
             (d.dcl_5V, 1.0), (d.dcl_3V3, 1.0)), output=True)
        dcs = tester.DcSubStep(setting=((d.dcs_PwrOn, 12.0), ), output=True)
        msr = tester.MeasureSubStep(
            (m.dmm_AcSwOn, m.ui_YesNoFan, m.dmm_24V, m.dmm_15V, m.dmm_12V,
             m.dmm_5V, m.dmm_3V3, m.dmm_5Vi, m.dmm_PGood, ), timeout=5)
        self.pwr_on = tester.SubStep((ld, dcs, msr))
        # Full Load: Apply full load, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_24V, 13.5), (d.dcl_15V, 7.5), (d.dcl_12V, 20.0),
             (d.dcl_5V, 10.0), (d.dcl_3V3, 5.0)))
        msr = tester.MeasureSubStep(
            (m.dmm_24V, m.dmm_15V, m.dmm_12V, m.dmm_5V, m.dmm_3V3, m.dmm_5Vi,
             m.dmm_PGood, ), timeout=5)
        self.full_load = tester.SubStep((ld, msr))
