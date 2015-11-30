#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *
from .. import console

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
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_vin = dcsource.DCSource(devices['DCS2'])
        # Power for Awnings.
        self.dcs_awn = dcsource.DCSource(devices['DCS3'])
        self.rla_reset = relay.Relay(devices['RLA1'])
        self.rla_boot = relay.Relay(devices['RLA2'])
        self.rla_awnA = relay.Relay(devices['RLA3'])
        self.rla_awnB = relay.Relay(devices['RLA4'])
        self.rla_sldA = relay.Relay(devices['RLA5'])
        self.rla_sldB = relay.Relay(devices['RLA6'])
        self.rla_s1 = relay.Relay(devices['RLA7'])
        self.rla_s2 = relay.Relay(devices['RLA8'])
        self.rla_s3 = relay.Relay(devices['RLA9'])
        self.rla_s4 = relay.Relay(devices['RLA10'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_vin, self.dcs_vcom, self.dcs_awn):
            dcs.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_awnA,
                    self.rla_awnB, self.rla_sldA, self.rla_sldB,
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
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oAwnA = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.oAwnB = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self.oSldA = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.01)
        self.oSldB = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=translate('cn101_initial', 'msgSnEntry'),
            caption=translate('cn101_initial', 'capSnEntry'))
        self.oCANID = console.Sensor(
            cn101, 'CAN_ID', rdgtype=tester.sensor.ReadingString)
        self.oCANBIND = console.Sensor(cn101, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            cn101, 'SwVer', rdgtype=tester.sensor.ReadingString)
        self.oBtMac = console.Sensor(
            cn101, 'BtMac', rdgtype=tester.sensor.ReadingString)
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
        self.program = Measurement(limits['Program'], sense.oMirARM)
        self.detectBT = Measurement(limits['DetectBT'], sense.oMirBT)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_awnAOff = Measurement(limits['AwnOff'], sense.oAwnA)
        self.dmm_awnBOff = Measurement(limits['AwnOff'], sense.oAwnB)
        self.dmm_awnAOn = Measurement(limits['AwnOn'], sense.oAwnA)
        self.dmm_awnBOn = Measurement(limits['AwnOn'], sense.oAwnB)
        self.dmm_sldAOff = Measurement(limits['SldOutOff'], sense.oSldA)
        self.dmm_sldBOff = Measurement(limits['SldOutOff'], sense.oSldB)
        self.dmm_sldAOn = Measurement(limits['SldOutOn'], sense.oSldA)
        self.dmm_sldBOn = Measurement(limits['SldOutOn'], sense.oSldB)
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
            setting=((d.dcs_vcom, 12.0), (d.dcs_vin, 12.75)), output=True)
        msr1 = MeasureSubStep((m.dmm_vin, m.dmm_3v3), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
        # Awning:
        dcs1 = DcSubStep(setting=((d.dcs_awn, 12.3), ), output=True)
        rly1 = RelaySubStep(
            relays=((d.rla_awnA, True), (d.rla_awnB, True),
                    (d.rla_sldA, True), (d.rla_sldB, True)))
        msr1 = MeasureSubStep((m.dmm_awnAOn, m.dmm_awnBOn, m.dmm_sldAOn,
                              m.dmm_sldBOn), timeout=5)
        rly2 = RelaySubStep(
            relays=((d.rla_awnA, False), (d.rla_awnB, False),
                    (d.rla_sldA, False), (d.rla_sldB, False)))
        msr2 = MeasureSubStep((m.dmm_awnAOff, m.dmm_awnBOff, m.dmm_sldAOff,
                              m.dmm_sldBOff), timeout=5)
        self.motorcontrol = Step((dcs1, rly1, msr1, rly2, msr2))
