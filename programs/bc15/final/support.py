#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor
translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcl = dcload.DCLoad(devices['DCL1'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.vout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.ps_mode = sensor.Notify(
            message=translate('bc15_final', 'GoToPsMode'),
            caption=translate('bc15_final', 'capPsMode'))
        self.ch_mode = sensor.Notify(
            message=translate('bc15_final', 'GoToChargeMode'),
            caption=translate('bc15_final', 'capChargeMode'))
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.vout,
            detect_limit=(limits['InOCP'], ),
            start=10.0, stop=17.0, step=0.5, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.vout_nl = Measurement(limits['VoutNL'], sense.vout)
        self.vout = Measurement(limits['Vout'], sense.vout)
        self.ps_mode = Measurement(limits['Notify'], sense.ps_mode)
        self.ch_mode = Measurement(limits['Notify'], sense.ch_mode)
        self.ocp = Measurement(limits['OCP'], sense.ocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerOn:
        #   Apply 240Vac, enter Power Supply mode, set load, measure.
        ld1 = LoadSubStep(((d.dcl, 1.0), ), output=True)
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=1.0)
        msr1 = MeasureSubStep((m.ps_mode, m.vout_nl, ), timeout=5)
        self.pwr_on = Step((ld1, acs1, msr1, ))
        # Loaded:
        #   Apply 10A load, measure, enter Charger mode
        ld10 = LoadSubStep(((d.dcl, 10.0), ), output=True)
        msr10 = MeasureSubStep((m.vout, m.ocp, m.ch_mode, ), timeout=5)
        self.load = Step((ld10, msr10, ))