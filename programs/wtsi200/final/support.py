#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WTSI200 Final Test Program."""

from pydispatch import dispatcher
import time

import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dso = dso.DSO(devices['DSO'])
        self.dcs_12V = dcsource.DCSource(devices['DCS1'])
        self.dcs_3V3 = dcsource.DCSource(devices['DCS2'])
        self.rla_tank1S3 = relay.Relay(devices['RLA1'])
        self.rla_tank1S2 = relay.Relay(devices['RLA2'])
        self.rla_tank1S1 = relay.Relay(devices['RLA3'])
        self.rla_tank2S3 = relay.Relay(devices['RLA4'])
        self.rla_tank2S2 = relay.Relay(devices['RLA5'])
        self.rla_tank2S1 = relay.Relay(devices['RLA6'])
        self.rla_tank3S3 = relay.Relay(devices['RLA7'])
        self.rla_tank3S2 = relay.Relay(devices['RLA8'])
        self.rla_tank3S1 = relay.Relay(devices['RLA9'])
        self.rla_trigg = relay.Relay(devices['RLA10'])
        self._all_relays = (
            self.rla_tank1S3, self.rla_tank1S2, self.rla_tank1S1,
            self.rla_tank2S3, self.rla_tank2S2, self.rla_tank2S1,
            self.rla_tank3S3, self.rla_tank3S2, self.rla_tank3S1,
            self.rla_trigg)

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_12V, self.dcs_3V3):
            dcs.output(0.0, False)
        for rla in self._all_relays:
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dso = logical_devices.dso
        tbase = sensor.Timebase(
            range=0.20, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=4, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = ()
        for ch in range(1, 4):
            rdgs += (sensor.Vtim(ch=ch, time_point=0.06), )
        chans = ()
        for ch in range(1, 5):
            chans += (sensor.Channel(
                ch=ch, mux=1, range=4.0, offset=(1.5 + ch * 0.1),
                dc_coupling=True, att=1, bwlim=True), )
        self.oTankLevels = sensor.DSO(
            dso, chans, tbase, trg, rdgs, single=True)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        lims = {
            'tankL1': (
                limits['T1level1'], limits['T2level1'], limits['T3level1']),
            'tank1L2': (
                limits['level2'], limits['level1'], limits['level1']),
            'tank1L3': (
                limits['level3'], limits['level1'], limits['level1']),
            'tank1L4': (
                limits['level4'], limits['level1'], limits['level1']),
            'tank2L2': (
                limits['level1'], limits['level2'], limits['level1']),
            'tank2L3': (
                limits['level1'], limits['level3'], limits['level1']),
            'tank2L4': (
                limits['level1'], limits['level4'], limits['level1']),
            'tank3L2': (
                limits['level1'], limits['level1'], limits['level2']),
            'tank3L3': (
                limits['level1'], limits['level1'], limits['level3']),
            'tank3L4': (
                limits['level1'], limits['level1'], limits['level4'])
            }
        self.dso_TankLevel1 = Measurement(
            lims['tankL1'], sense.oTankLevels)
        self.dso_Tank1Level2 = Measurement(
            lims['tank1L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank1Level3 = Measurement(
            lims['tank1L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank1Level4 = Measurement(
            lims['tank1L4'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level2 = Measurement(
            lims['tank2L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level3 = Measurement(
            lims['tank2L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level4 = Measurement(
            lims['tank2L4'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level2 = Measurement(
            lims['tank3L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level3 = Measurement(
            lims['tank3L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level4 = Measurement(
            lims['tank3L4'], sense.oTankLevels, autoconfig=False)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        self.d = d
        m = measurements
        dispatcher.connect(
            self.dso_trigger,
            sender=m.dso_TankLevel1.sensor,
            signal=tester.SigDso)
        # PowerOn: Apply 12Vdc, measure.
        dcs = DcSubStep(
            setting=((d.dcs_12V, 12.0), (d.dcs_3V3, 3.3), ),
            output=True, delay=1)
        msr = MeasureSubStep((m.dso_TankLevel1, ))
        self.pwr_on = Step((dcs, msr, ))
        # Tank1: Vary levels, measure.
        rly1 = RelaySubStep(((d.rla_tank1S3, True), ))
        msr1 = MeasureSubStep((m.dso_Tank1Level2, ))
        rly2 = RelaySubStep(((d.rla_tank1S2, True), ))
        msr2 = MeasureSubStep((m.dso_Tank1Level3, ))
        rly3 = RelaySubStep(((d.rla_tank1S1, True), ))
        msr3 = MeasureSubStep((m.dso_Tank1Level4, ))
        rly4 = RelaySubStep(
            ((d.rla_tank1S3, False), (d.rla_tank1S2, False),
             (d.rla_tank1S1, False)))
        self.tank1 = Step((rly1, msr1, rly2, msr2, rly3, msr3, rly4))
        # Tank2: Vary levels, measure.
        rly1 = RelaySubStep(((d.rla_tank2S3, True), ))
        msr1 = MeasureSubStep((m.dso_Tank2Level2, ))
        rly2 = RelaySubStep(((d.rla_tank2S2, True), ))
        msr2 = MeasureSubStep((m.dso_Tank2Level3, ))
        rly3 = RelaySubStep(((d.rla_tank2S1, True), ))
        msr3 = MeasureSubStep((m.dso_Tank2Level4, ))
        rly4 = RelaySubStep(
            ((d.rla_tank2S3, False), (d.rla_tank2S2, False),
             (d.rla_tank2S1, False)))
        self.tank2 = Step((rly1, msr1, rly2, msr2, rly3, msr3, rly4))
        # Tank3: Vary levels, measure.
        rly1 = RelaySubStep(((d.rla_tank3S3, True), ))
        msr1 = MeasureSubStep((m.dso_Tank3Level2, ))
        rly2 = RelaySubStep(((d.rla_tank3S2, True), ))
        msr2 = MeasureSubStep((m.dso_Tank3Level3, ))
        rly3 = RelaySubStep(((d.rla_tank3S1, True), ))
        msr3 = MeasureSubStep((m.dso_Tank3Level4, ))
        rly4 = RelaySubStep(
            ((d.rla_tank3S3, False), (d.rla_tank3S2, False),
             (d.rla_tank3S1, False)))
        self.tank3 = Step((rly1, msr1, rly2, msr2, rly3, msr3, rly4))

    def dso_trigger(self):
        """DSO Ready handler."""
        self.d.rla_trigg.set_on()
        time.sleep(0.25)
        self.d.rla_trigg.set_off()
