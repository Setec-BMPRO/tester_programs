#!/usr/bin/env python3
"""Trs1 Initial Test Program.

        Logical Devices
        Sensors
        Measurements

"""
from pydispatch import dispatcher

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

        self.dcs_Vin = dcsource.DCSource(devices['DCS1'])

        self.rla_ = relay.Relay(devices['RLA1'])   # ON == Asserted


    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_Vin, ):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_, ):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        # Mirror sensor for Programming result logging
        self.oMirARM = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        tester.TranslationContext = 'trs1_initial'
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensor."""
        self.oMirARM.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)


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
        dcs1 = DcSubStep(
            setting=((d.dcs_Vin, 12.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_Vin, ), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
