#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from .. import console

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
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_vin = dcsource.DCSource(devices['DCS2'])
        # Power for Awning.
        self.dcs_awn = dcsource.DCSource(devices['DCS3'])
        self.rla_reset = relay.Relay(devices['RLA1'])
        self.rla_boot = relay.Relay(devices['RLA2'])
        self.rla_awn = relay.Relay(devices['RLA3'])
        self.rla_s1 = relay.Relay(devices['RLA4'])
        self.rla_s2 = relay.Relay(devices['RLA5'])
        self.rla_s3 = relay.Relay(devices['RLA6'])
        self.rla_s4 = relay.Relay(devices['RLA7'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_vin, self.dcs_vcom, self.dcs_awn):
            dcs.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_awn,
                    self.rla_s1, self.rla_s2, self.rla_s3, self.rla_s4):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, cn101):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits
           @param cn101 cn101 ARM console driver

        """
        dmm = logical_devices.dmm
        # Mirror sensor for Programming result logging
        self.oMirARM = sensor.Mirror()
        self.oMirBT = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.microsw = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self.sw1 = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self.sw2 = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oAwnA = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.01)
        self.oAwnB = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=translate('cn101_initial', 'msgSnEntry'),
            caption=translate('cn101_initial', 'capSnEntry'))
        self.oCANID = console.Sensor(
            cn101, 'CAN_ID', rdgtype=sensor.ReadingString)
        self.oCANBIND = console.Sensor(cn101, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            cn101, 'SwVer', rdgtype=sensor.ReadingString)
        self.oBtMac = console.Sensor(
            cn101, 'BtMac', rdgtype=sensor.ReadingString)
        self.tank1 = console.Sensor(cn101, 'TANK1')
        self.tank2 = console.Sensor(cn101, 'TANK2')
        self.tank3 = console.Sensor(cn101, 'TANK3')
        self.tank4 = console.Sensor(cn101, 'TANK4')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensor."""
        self.oMirARM.flush()
        self.oMirBT.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_microsw = Measurement(limits['Part'], sense.microsw)
        self.dmm_sw1 = Measurement(limits['Part'], sense.sw1)
        self.dmm_sw2 = Measurement(limits['Part'], sense.sw2)
        self.program = Measurement(limits['Program'], sense.oMirARM)
        self.detectBT = Measurement(limits['DetectBT'], sense.oMirBT)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_awnAOff = Measurement(limits['AwnOff'], sense.oAwnA)
        self.dmm_awnBOff = Measurement(limits['AwnOff'], sense.oAwnB)
        self.dmm_awnAOn = Measurement(limits['AwnOn'], sense.oAwnA)
        self.dmm_awnBOn = Measurement(limits['AwnOn'], sense.oAwnB)
        self.ui_serialnum = Measurement(limits['SerNum'], sense.oSnEntry)
        self.cn101_can_id = Measurement(limits['CAN_ID'], sense.oCANID)
        self.cn101_can_bind = Measurement(limits['CAN_BIND'], sense.oCANBIND)
        self.cn101_swver = Measurement(limits['SwVer'], sense.oSwVer)
        self.cn101_btmac = Measurement(limits['BtMac'], sense.oBtMac)
        self.cn101_s1 = Measurement(limits['Tank'], sense.tank1)
        self.cn101_s2 = Measurement(limits['Tank'], sense.tank2)
        self.cn101_s3 = Measurement(limits['Tank'], sense.tank3)
        self.cn101_s4 = Measurement(limits['Tank'], sense.tank4)


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
            setting=((d.dcs_vin, 8.6), ), output=True)
        msr1 = MeasureSubStep((m.dmm_vin, m.dmm_3v3), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
        # PowerReset:
        dcs1 = DcSubStep(
            setting=((d.dcs_vin, 0.0), ), delay=0.5)
        dcs2 = DcSubStep(
            setting=((d.dcs_vin, 12.0), ), delay=5.0)
        self.rst = Step((dcs1, dcs2, ))
        # Awning:
        dcs1 = DcSubStep(setting=((d.dcs_awn, 13.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_awnAOff, m.dmm_awnBOff), timeout=5)
        rly1 = RelaySubStep(relays=((d.rla_awn, True), ))
        msr2 = MeasureSubStep((m.dmm_awnAOn, m.dmm_awnBOn), timeout=5)
        rly2 = RelaySubStep(relays=((d.rla_awn, False), ))
        dcs2 = DcSubStep(setting=((d.dcs_awn, 0.0), ))
        self.awn = Step((dcs1, msr1, rly1, msr2, rly2, dcs2))

        # TankSense:
        rly1 = RelaySubStep(relays=((d.rla_s1, True), (d.rla_s2, True),
                            (d.rla_s3, True), (d.rla_s4, True), ), delay=0.2)
        msr1 = MeasureSubStep(
                    (m.cn101_s1, m.cn101_s2, m.cn101_s3, m.cn101_s4), timeout=5)
        self.tank = Step((rly1, msr1,))
