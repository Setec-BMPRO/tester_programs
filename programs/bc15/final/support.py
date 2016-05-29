#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import tester
import sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl = tester.DCLoad(devices['DCL1'])

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
            message=tester.translate('bc15_final', 'GoToPsMode'),
            caption=tester.translate('bc15_final', 'capPsMode'))
        self.ch_mode = sensor.Notify(
            message=tester.translate('bc15_final', 'GoToChargeMode'),
            caption=tester.translate('bc15_final', 'capChargeMode'))
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
        Measurement = tester.Measurement
        self.vout_nl = Measurement(limits['VoutNL'], sense.vout)
        self.vout = Measurement(limits['Vout'], sense.vout)
        self.ps_mode = Measurement(limits['Notify'], sense.ps_mode)
        self.ch_mode = Measurement(limits['Notify'], sense.ch_mode)
        self.ocp = Measurement(limits['OCP'], sense.ocp)
