#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_photo = tester.DCSource(devices['DCS1'])
        self.dcl_out = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_photo.output(0.0, False)
        self.dcl_out.output(0.0, False)

class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.photo = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.vload1 = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        # Generate load voltage sensors
        self.vloads = []
        for i in range(limits['LOAD_COUNT'].limit):
            s = sensor.Vdc(dmm, high=i + 5, low=3, rng=100, res=0.001)
            self.vloads.append(s)
        low, high = limits['OCP'].limit
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_out, sensor=self.vload1,
            detect_limit=(limits['InOCP'], ),
            start=low - 1, stop=high + 1, step=0.5, delay=0.2)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_fanoff = Measurement(limits['FanOff'], sense.photo)
        self.dmm_fanon = Measurement(limits['FanOn'], sense.photo)
        # Generate load voltage measurements
        self.dmm_vouts = ()
        for sen in sense.vloads:
            m = Measurement(limits['Vout'], sen)
            self.dmm_vouts += (m, )
        self.dmm_vloads = ()
        for sen in sense.vloads:
            m = Measurement(limits['Vload'], sen)
            self.dmm_vloads += (m, )
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
