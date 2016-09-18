#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Initial Test Program."""

import time
import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])
        self.discharge = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_24V.output(5.0)
        time.sleep(1)
        self.discharge.pulse()
        self.dcl_24V.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.ACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.PFC = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self.PriCtl = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self.PriVref = sensor.Vdc(dmm, high=5, low=2, rng=10, res=0.001)
        self.o24V = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.Fan12V = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.SecCtl = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.01)
        self.SecVref = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self.Lock = sensor.Res(dmm, high=10, low=5, rng=10000, res=0.1)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_24V, sensor=self.o24V,
            detect_limit=(limits['inOCP'], ),
            start=15.0, stop=22.0, step=0.05, delay=0.05)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_ACin = Measurement(limits['ACin'], sense.ACin)
        self.dmm_PFC = Measurement(limits['PFC'], sense.PFC)
        self.dmm_PriCtl = Measurement(limits['PriCtl'], sense.PriCtl)
        self.dmm_PriVref = Measurement(limits['PriVref'], sense.PriVref)
        self.dmm_24Vnl = Measurement(limits['24Vnl'], sense.o24V)
        self.dmm_24Vfl = Measurement(limits['24Vfl'], sense.o24V)
        self.dmm_Fan12V = Measurement(limits['Fan12V'], sense.Fan12V)
        self.dmm_SecCtl = Measurement(limits['SecCtl'], sense.SecCtl)
        self.dmm_SecVref = Measurement(limits['SecVref'], sense.SecVref)
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.Lock)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 92Vac, measure.
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=92.0, output=True, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_ACin, ), timeout=5, delay=2)
        msr2 = tester.MeasureSubStep(
            (m.dmm_PFC, m.dmm_PriCtl, m.dmm_PriVref, m.dmm_24Vnl,
             m.dmm_Fan12V, m.dmm_SecCtl, m.dmm_SecVref, ), timeout=5)
        self.pwr_up = tester.SubStep((acs1, msr1, msr2))
        # FullLoad: Apply 240Vac, load, measure.
        acs = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        ld = tester.LoadSubStep(((d.dcl_24V, 15.0), ), output=True)
        msr = tester.MeasureSubStep((m.dmm_24Vfl, ), timeout=5)
        self.full_load = tester.SubStep((acs, ld, msr))
