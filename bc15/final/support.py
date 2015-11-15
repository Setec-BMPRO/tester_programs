#!/usr/bin/env python3
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

        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        tester.TranslationContext = 'bc15_final'
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerOn: Apply 240Vac, set min load, measure.
        ld1 = LoadSubStep(((d.dcl, 1.0), ), output=True)
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=1.0)
        msr1 = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        self.pwr_on = Step((ld1, acs1, msr1, ))
