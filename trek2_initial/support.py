#!/usr/bin/env python3
"""Trek2 Initial Test Program.

        Logical Devices
        Sensors
        Measurements

"""
from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *
import share.trek2

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
        # Power RS232 + Fixture Trek2.
        self.dcs_Vcom = dcsource.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_Vin = dcsource.DCSource(devices['DCS2'])
        self.rla_reset = relay.Relay(devices['RLA1'])   # ON == Asserted
        self.rla_boot = relay.Relay(devices['RLA2'])    # ON == Asserted


    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_Vin, self.dcs_Vcom):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_reset, self.rla_boot):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, trek2):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits
           @param trek2 Trek2 ARM console driver

        """
        dmm = logical_devices.dmm
        # Mirror sensor for Programming result logging
        self.oMirARM = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oBkLght = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        tester.TranslationContext = 'trek2_initial'
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))
        self.oCANID = share.trek2.Sensor(
            trek2, 'CAN_ID', rdgtype=tester.sensor.ReadingString)

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
        self.pgmARM = Measurement(limits['Program'], sense.oMirARM)
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_BkLghtOff = Measurement(limits['BkLghtOff'], sense.oBkLght)
        self.dmm_BkLghtOn = Measurement(limits['BkLghtOn'], sense.oBkLght)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.trek2_can_id = Measurement(limits['CAN_ID'], sense.oCANID)


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
            setting=((d.dcs_Vcom, 12.0), (d.dcs_Vin, 12.75)), output=True)
        msr1 = MeasureSubStep((m.dmm_Vin, m.dmm_3V3), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
