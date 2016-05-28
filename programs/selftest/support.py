#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program."""

import sensor
import tester
from tester.devlogical import *

Measurement = tester.measure.Measurement


class LogicalDevices(object):

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dso = dso.DSO(devices['DSO'])
        # DC Sources
        dcs1 = dcsource.DCSource(devices['DCS1'])
        dcs2 = dcsource.DCSource(devices['DCS2'])
        dcs3 = dcsource.DCSource(devices['DCS3'])
        dcs4 = dcsource.DCSource(devices['DCS4'])
        dcs5 = dcsource.DCSource(devices['DCS5'])
        dcs6 = dcsource.DCSource(devices['DCS6'])
        dcs7 = dcsource.DCSource(devices['DCS7'])
        self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5, dcs6, dcs7)
        # AC Source
        self.acs = acsource.ACSource(devices['ACS'])
        # DC Loads
        dcl1 = dcload.DCLoad(devices['DCL1'])
        dcl2 = dcload.DCLoad(devices['DCL2'])
        dcl3 = dcload.DCLoad(devices['DCL3'])
        dcl4 = dcload.DCLoad(devices['DCL4'])
        dcl5 = dcload.DCLoad(devices['DCL5'])
        dcl6 = dcload.DCLoad(devices['DCL6'])
        dcl7 = dcload.DCLoad(devices['DCL7'])
        self.dcl = (dcl1, dcl2, dcl3, dcl4, dcl5, dcl6, dcl7)
        # Relay Drivers
        self.rly = []
        for num in range(1, 23):
            self.rly.append(relay.Relay(devices['RLA{}'.format(num)]))
        # Discharge
        self.disch = discharge.Discharge(devices['DIS'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.acs.output(voltage=0.0, output=False)
        for ld in self.dcl:
            ld.output(0.0)
        for dcs in self.dcs:
            dcs.output(0.0, False)
        for rla in self.rly:
            rla.set_off()


class Sensors(object):

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        # Self Checker Voltages
        self.check12 = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.1)
        check5a = sensor.Vdc(dmm, high=2, low=3, rng=10, res=0.1)
        check5b = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.1)
        check5c = sensor.Vdc(dmm, high=4, low=3, rng=10, res=0.1)
        check5d = sensor.Vdc(dmm, high=15, low=3, rng=10, res=0.1)
        check5e = sensor.Vdc(dmm, high=16, low=3, rng=10, res=0.1)
        self.check5 = (check5a, check5b, check5c, check5d, check5e)
        # DSO
        shield1 = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.1)
        shield2 = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.1)
        shield3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.1)
        shield4 = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.1)
        self.shield = (shield1, shield2, shield3, shield4)
        tbase = sensor.Timebase(range=0.10, main_mode=True, delay=0,
                                centre_ref=True)
        trg = sensor.Trigger(ch=1, level=1.0, normal_mode=False,
                             pos_slope=True)
        rdgs = []
        for ch in range(1, 5):
            rdgs.append(sensor.Vavg(ch=ch))
        subchans1 = []
        for ch in range(1, 5):
            subchans1.append(sensor.Channel(ch=ch, mux=1, range=40.0,
                             offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan1 = sensor.DSO(dso, subchans1, tbase, trg, rdgs)
        subchans2 = []
        for ch in range(1, 5):
            subchans2.append(sensor.Channel(ch=ch, mux=2, range=40.0,
                             offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan2 = sensor.DSO(dso, subchans2, tbase, trg, rdgs)
        subchans3 = []
        for ch in range(1, 5):
            subchans3.append(sensor.Channel(ch=ch, mux=3, range=40.0,
                             offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan3 = sensor.DSO(dso, subchans3, tbase, trg, rdgs)
        subchans4 = []
        for ch in range(1, 5):
            subchans4.append(sensor.Channel(ch=ch, mux=4, range=40.0,
                             offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan4 = sensor.DSO(dso, subchans4, tbase, trg, rdgs)
        self.subchan = (subchan1, subchan2, subchan3, subchan4)
        # DC Sources
        dcs1 = sensor.Vdc(dmm, high=18, low=8, rng=100, res=0.001)
        dcs2 = sensor.Vdc(dmm, high=19, low=8, rng=100, res=0.001)
        dcs3 = sensor.Vdc(dmm, high=20, low=8, rng=100, res=0.001)
        dcs4 = sensor.Vdc(dmm, high=21, low=8, rng=100, res=0.001)
        dcs5 = sensor.Vdc(dmm, high=22, low=8, rng=100, res=0.001)
        dcs6 = sensor.Vdc(dmm, high=23, low=8, rng=100, res=0.001)
        dcs7 = sensor.Vdc(dmm, high=24, low=8, rng=100, res=0.001)
        self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5, dcs6, dcs7)
        # AC Sources
        self.Acs = sensor.Vac(dmm, high=14, low=4, rng=300, res='MAX')
        # DC Loads
        self.Shunt = sensor.Vdc(dmm, high=6, low=2, rng=0.1, res=0.001)
        # Relay Drivers
        self.Rla12V = sensor.Vdc(dmm, high=17, low=1, rng=100, res=0.1)
        self.Rla = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        # Discharge
        disch1 = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.1)
        disch2 = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.1)
        disch3 = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.1)
        self.disch = (disch1, disch2, disch3)


class Measurements(object):

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        # Self Checker Voltages
        self.dmm_check_v = []
        self.dmm_check_v.append(Measurement(limits['12V'], sense.check12))
        for s in sense.check5:
            self.dmm_check_v.append(Measurement(limits['5V'], s))
        # DSO
        self.dmm_shield_off = []
        for s in sense.shield:
            self.dmm_shield_off.append(Measurement(limits['ShieldOFF'], s))
        self.dmm_shield_on = []
        for s in sense.shield:
            self.dmm_shield_on.append(Measurement(limits['ShieldON'], s))
        self.dso_subchan = []
        lims = (limits['Dso8'], limits['Dso6'], limits['Dso4'], limits['Dso2'])
        for s in sense.subchan:
            self.dso_subchan.append(Measurement(lims, s))
        # DC Sources
        dcs_05 = []
        dcs_10 = []
        dcs_20 = []
        dcs_35 = []
        for s in sense.dcs:
            dcs_05.append(Measurement(limits['Dcs5'], s))
            dcs_10.append(Measurement(limits['Dcs10'], s))
            dcs_20.append(Measurement(limits['Dcs20'], s))
            dcs_35.append(Measurement(limits['Dcs35'], s))
        self.dmm_dcs = ((5.0, dcs_05), (10.0, dcs_10), (20.0, dcs_20),
                        (35.0, dcs_35))
        # AC Source
        self.dmm_Acs = ((120.0, Measurement(limits['Acs120'], sense.Acs)),
                        (240.0, Measurement(limits['Acs240'], sense.Acs)))
        # DC Loads
        self.dmm_Shunt = ((5, Measurement(limits['Dcl05'], sense.Shunt)),
                          (10, Measurement(limits['Dcl10'], sense.Shunt)),
                          (20, Measurement(limits['Dcl20'], sense.Shunt)),
                          (40, Measurement(limits['Dcl40'], sense.Shunt)))
        # Relay Drivers
        self.dmm_Rla12V = Measurement(limits['Rla12V'], sense.Rla12V)
        self.dmm_RlaOn = Measurement(limits['RlaOn'], sense.Rla)
        self.dmm_RlaOff = Measurement(limits['RlaOff'], sense.Rla)
        # Discharge
        self.dmm_disch_on = []
        for s in sense.disch:
            self.dmm_disch_on.append(Measurement(limits['Disch_on'], s))
        self.dmm_disch_off = []
        for s in sense.disch:
            self.dmm_disch_off.append(Measurement(limits['Disch_off'], s))
