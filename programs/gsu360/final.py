#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Final Test Program."""

import time
import tester

LIMITS = tester.testlimit.limitset((
    ('24V', 1, 23.40, 24.60, None, None),
    ('24Vinocp', 1, 23.4, None, None, None),
    ('24Vocp', 1, 15.5, 20.0, None, None),
    ('24Voff', 1, 5.0, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """GSU360-1TA Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Shutdown', self._step_shutdown),
            tester.TestStep('Restart', self._step_restart),
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
        """Power up unit at 240Vac."""
        self.fifo_push(((s.o24V, 24.00), (s.oYesNoGreen, True)))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.o24V, 24.10), (s.o24V, 24.00)))
        d.dcl_24V.binary(0.0, 15.0, 4.0)
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o24V, (24.1, ) * 15 + (22.0, ), ), ))
        # Load is already at 15.0A
        m.ramp_24Vocp.measure()

    def _step_shutdown(self):
        """Overload unit, measure."""
        self.fifo_push(((s.o24V, 4.0), ))
        # Shutdown: Overload unit, measure
        # Load is already at OCP point
        d.dcl_24V.output(21.0)
        m.dmm_24Voff.measure(timeout=5)

    def _step_restart(self):
        """Re-Start unit after Shutdown."""
        self.fifo_push(((s.o24V, 24.0), ))
        d.dcl_24V.output(0.0)
        m.dmm_24V.measure(timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        self.dcl_24V.output(5.0, True)
        time.sleep(20.0)    # Allow time to discharge
        self.dcl_24V.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('gsu360_final', 'IsSwitchGreen?'),
            caption=tester.translate('gsu360_final', 'capSwitchGreen'))
        self.o24Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_24V, sensor=self.o24V,
            detect_limit=(limits['24Vinocp'], ),
            start=15.0, stop=20.5, step=0.1, delay=0.1, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ramp_24Vocp = Measurement(limits['24Vocp'], sense.o24Vocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, measure.
        ld = tester.LoadSubStep(((d.dcl_24V, 0.5),), output=True)
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = tester.MeasureSubStep((m.dmm_24V, m.ui_YesNoGreen), timeout=5)
        self.pwr_up = tester.SubStep((ld, acs, msr))
        # Full Load: measure, 110Vac, measure, 240Vac.
        msr1 = tester.MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=110.0)
        msr2 = tester.MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs2 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        self.full_load = tester.SubStep((msr1, acs1, msr2, acs2))
