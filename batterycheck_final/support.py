#!/usr/bin/env python3
"""BatteryCheck Final Test Program."""

from pydispatch import dispatcher

import tester.measure
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor
translate = tester.translate


class LogicalDevices(object):

    """BatteryCheck Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_input = dcsource.DCSource(devices['DCS1'])

    def reset(self):
        """Reset instruments."""
        # Switch off DC Source
        self.dcs_input.output(0.0, output=False)

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()


class Sensors(object):

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        tester.TranslationContext = 'batterycheck_final'
        self.oMirBT = sensor.Mirror()
        self.oMirSwVer = sensor.Mirror(rdgtype=tester.sensor.ReadingString)
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.o12V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirBT.flush()
        self.oMirSwVer.flush()


class Measurements(object):

    """BatteryCheck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.BTscan = Measurement(limits['BTscan'], sense.oMirBT)
        self.BTpair = Measurement(limits['BTpair'], sense.oMirBT)
        self.SerNumARM = Measurement(limits['ARMSerNum'], sense.oMirBT)
        self.SwVerARM = Measurement(limits['ARMSwVer'], sense.oMirSwVer)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements

        # PowerUp:
        dcs1 = DcSubStep(setting=((d.dcs_input, 12.0),), output=True)
        msr1 = MeasureSubStep((m.dmm_12V, ), timeout=5)
        self.pwr_up = Step((dcs1, msr1))
