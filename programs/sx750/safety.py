#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Safety Test Program.

Call 'self.abort()' to stop program running at end of current step.
'self._result_map' is a list of 'uut.Result' indexed by position.

"""

import tester

LIMITS = tester.testlimit.limitset((
    ('gnd', 0, 20, 100, None, None),
    ('arc', 0, -0.001, 0, None, None),
    ('acw', 0, 2.0, 4.0, None, None),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Safety(tester.TestSequence):

    """SX-750 Safety Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('Gnd1', self._step_gnd1),
            tester.TestStep('Gnd2', self._step_gnd2),
            tester.TestStep('Gnd3', self._step_gnd3),
            tester.TestStep('HiPot', self._step_hipot),
            )
        global m, d, s
        d = LogicalDevices(self._devices)
        s = Sensors(d)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_gnd1(self):
        """Ground Continuity 1."""
        self.fifo_push(((s.gnd1, 40), ))
        m.gnd1.measure()

    def _step_gnd2(self):
        """Ground Continuity 2."""
        self.fifo_push(((s.gnd2, 50), ))
        m.gnd2.measure()

    def _step_gnd3(self):
        """Ground Continuity 3."""
        self.fifo_push(((s.gnd3, 60), ))
        m.gnd3.measure()

    def _step_hipot(self):
        """HiPot Test."""
        self.fifo_push(((s.acw, 3.0), ))
        m.acw.measure()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.st = tester.SafetyTester(devices['SAF'])

    def reset(self):
        """Reset instruments."""
        pass


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        st = logical_devices.st
        sensor = tester.sensor
        # Safety Tester sequence and test steps
        self.gnd1 = sensor.STGND(st, step=1, ch=1)
        self.gnd2 = sensor.STGND(st, step=2, ch=2, curr=11)
        self.gnd3 = sensor.STGND(st, step=3, ch=3, curr=11)
        self.acw = sensor.STACW(st, step=4)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.gnd1 = Measurement(limits['gnd'], sense.gnd1)
        self.gnd2 = Measurement(limits['gnd'], sense.gnd2)
        self.gnd3 = Measurement(limits['gnd'], sense.gnd3)
        self.acw = Measurement((limits['arc'], limits['acw']), sense.acw)
