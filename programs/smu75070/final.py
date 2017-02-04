#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMU750-70 Final Test Program."""

import tester

LIMITS = tester.testlimit.limitset((
    # 70 +/- 0.7
    ('70VOn', 1, 69.3, 70.7, None, None),
    ('70VOff', 1, -0.5, 69.2, None, None),
    # 11.5 +/- 0.1
    ('OCP', 1, 11.4, 11.6, None, None),
    ('inOCP', 1, 69.3, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """SMU750-70 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Shutdown', self._step_shutdown),
            )
        self._limits = LIMITS
        global d, s, m, t
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
        """Switch on at 240Vac, measure output at min load."""
        self.fifo_push(((s.o70V, 70.0), (s.oYesNoFan, True), ))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure output at full load (11.3A +/- 150mA)."""
        self.fifo_push(((s.o70V, 70.0), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o70V, (70.0, ) * 15 + (69.2, ), ), ))
        m.ramp_OCP.measure()

    def _step_shutdown(self):
        """Overload and shutdown unit, re-start."""
        self.fifo_push(((s.o70V, (10.0, 70.0)), ))
        t.shdn.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        dcl1 = tester.DCLoad(devices['DCL1'])
        dcl2 = tester.DCLoad(devices['DCL2'])
        dcl3 = tester.DCLoad(devices['DCL3'])
        dcl4 = tester.DCLoad(devices['DCL4'])
        self.dcl = tester.DCLoadParallel(
            ((dcl1, 1), (dcl2, 1), (dcl3, 1), (dcl4, 1)))

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
        self.o70V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self.oYesNoFan = sensor.YesNo(
            message=tester.translate('smu75070_final', 'IsFanOn?'),
            caption=tester.translate('smu75070_final', 'capFanOn'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.o70V,
            detect_limit=(limits['inOCP'], ),
            start=11.3, stop=11.8, step=0.01, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_70Von = Measurement(limits['70VOn'], sense.o70V)
        self.dmm_70Voff = Measurement(limits['70VOff'], sense.o70V)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Min load, 240Vac, measure.
        ld1 = tester.LoadSubStep(((d.dcl, 0.0), ), output=True)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=2.0)
        msr1 = tester.MeasureSubStep((m.dmm_70Von, m.ui_YesNoFan,), timeout=5)
        self.pwr_up = tester.SubStep((ld1, acs1, msr1))
        # Full Load: Full load, measure.
        ld1 = tester.LoadSubStep( ((d.dcl, 11.2), ), delay=1)
        msr1 = tester.MeasureSubStep((m.dmm_70Von, ), timeout=5)
        self.full_load = tester.SubStep((ld1, msr1))
        # Shutdown: Overload, restart, measure.
        ld1 = tester.LoadSubStep( ((d.dcl, 11.9), ))
        msr1 = tester.MeasureSubStep((m.dmm_70Voff, ), timeout=5)
        ld2 = tester.LoadSubStep( ((d.dcl, 0.0), ), delay=2)
        msr2 = tester.MeasureSubStep((m.dmm_70Von, ), timeout=10)
        self.shdn = tester.SubStep((ld1, msr1, ld2, msr2))
