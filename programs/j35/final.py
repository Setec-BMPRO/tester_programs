#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Final Test Program."""

import tester
from share import oldteststep
from tester.testlimit import (
    lim_hilo_delta, lim_lo, lim_hi, lim_hilo, lim_hilo_percent, lim_boolean)

COUNT_A = 7
CURRENT_A = 14.0
COUNT_BC = 14
CURRENT_BC = 28.0

_BASE_DATA = (
    lim_lo('FanOff', 1.0),
    lim_hi('FanOn', 10.0),
    lim_hilo_delta('Vout', 12.8, 0.2),
    lim_hilo_percent('Vload', 12.8, 5),
    lim_lo('InOCP', 11.6),
    )

LIMITS_A = tester.testlimit.limitset(_BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_A),
    lim_lo('LOAD_CURRENT', CURRENT_A),
    lim_hilo('OCP', 20.0, 25.0),
    ))

LIMITS_B = tester.testlimit.limitset(_BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0, 42.0),
    lim_boolean('J35C', False),
    ))

LIMITS_C = tester.testlimit.limitset(_BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0, 42.0),
    lim_boolean('J35C', True),
    ))

LIMITS = {      # Test limit selection keyed by open() parameter
    None: LIMITS_C,
    'A': LIMITS_A,
    'B': LIMITS_B,
    'C': LIMITS_C,
    }


class Final(tester.TestSequence):

    """J35 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        super().__init__()
        self.phydev = physical_devices
        self.limits = None
        self.logdev = None
        self.sensors = None
        self.meas = None

    def open(self, parameter):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('OCP', self._step_ocp),
            )
        self.limits = LIMITS[parameter]
        self.logdev = LogicalDevices(self.phydev)
        self.sensors = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensors, self.limits)

    def close(self):
        """Finished testing."""
        self.logdev = None
        self.sensors = None
        self.meas = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        dev.dcs_photo.output(12.0, True)
        mes.dmm_fanoff.measure(timeout=5)
        dev.acsource.output(240.0, output=True)
        mes.dmm_fanon.measure(timeout=15)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vouts[load].measure(timeout=5)

    @oldteststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev.dcl_out.output(0.0,  output=True)
        dev.dcl_out.binary(1.0, self.limits['LOAD_CURRENT'].limit, 5.0)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vloads[load].measure(timeout=5)

    @oldteststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes.ramp_ocp.measure(timeout=5)


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
