#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Bias Initial Test Program."""

import time
import tester


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialBias(tester.TestSequence):

    """IDS-500 Initial Bias Test Program."""

    # Test limits
    limitdata = tester.testlimit.limitset((
        ('400V', 1, 390, 410, None, None),
        ('PVcc', 1, 12.8, 14.5, None, None),
        ('12VsbRaw', 1, 12.7, 13.49, None, None),
        ('OCP Trip', 1, 12.6, None, None, None),
        ('InOCP', 1, 12.6, None, None, None),
        ('OCP', 1, 1.2, 2.1, None, None),
        ('FixtureLock', 0, 20, None, None, None),
        ))

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('OCP', self._step_ocp),
            )
        self._limits = self.limitdata
        global d, m, s
        d = LogicalDevBias(self.physical_devices, self.fifo)
        s = SensorBias(d, self._limits)
        m = MeasureBias(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
#        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), (s.oPVcc, 14.0), ))
        m.dmm_lock.measure(timeout=5)
        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup((m.dmm_400V, m.dmm_pvcc, ),timeout=5)

    def _step_ocp(self):
        """Measure OCP."""
#        self.fifo_push(((s.o12Vsbraw, (13.0, ) * 4 + (12.5, 0.0), ), ))
        tester.MeasureGroup(
                (m.dmm_12Vsbraw, m.ramp_OCP, m.dmm_12Vsbraw2,),timeout=1)


class LogicalDevBias():

    """Bias Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_12Vsbraw = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        time.sleep(2)
        self.discharge.pulse()
        self.dcs_fan.output(0.0, False)
        self.dcl_12Vsbraw.output(0.0, False)


class SensorBias():

    """Bias Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.o400V = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self.oPVcc = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.o12Vsbraw = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_12Vsbraw, sensor=self.o12Vsbraw,
            detect_limit=(limits['InOCP'], ),
            start=1.5, stop=2.3, step=0.1, delay=0.1, reset=False)


class MeasureBias():

    """Bias Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_400V = Measurement(limits['400V'], sense.o400V)
        self.dmm_pvcc = Measurement(limits['PVcc'], sense.oPVcc)
        self.dmm_12Vsbraw = Measurement(limits['12VsbRaw'], sense.o12Vsbraw)
        self.dmm_12Vsbraw2 = Measurement(limits['OCP Trip'], sense.o12Vsbraw)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
