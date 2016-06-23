#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program."""

import sensor
import tester


class LogicalDevices(object):

    """Logical Devices."""

    def __init__(self, devices, is_ate2):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dso = tester.DSO(devices['DSO'])
        self.acsource = tester.ACSource(devices['ACS'])
        # DC Sources
        dcs1 = tester.DCSource(devices['DCS1'])
        dcs2 = tester.DCSource(devices['DCS2'])
        dcs3 = tester.DCSource(devices['DCS3'])
        dcs4 = tester.DCSource(devices['DCS4'])
        dcs5 = tester.DCSource(devices['DCS5'])
        if is_ate2:
            self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5)
        else:
            dcs6 = tester.DCSource(devices['DCS6'])
            dcs7 = tester.DCSource(devices['DCS7'])
            self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5, dcs6, dcs7)
        # DC Loads
        dcl1 = tester.DCLoad(devices['DCL1'])
        dcl2 = tester.DCLoad(devices['DCL2'])
        dcl3 = tester.DCLoad(devices['DCL3'])
        dcl4 = tester.DCLoad(devices['DCL4'])
        dcl5 = tester.DCLoad(devices['DCL5'])
        dcl6 = tester.DCLoad(devices['DCL6'])
        if is_ate2:
            self.dcl = (dcl1, dcl2, dcl3, dcl4, dcl5, dcl6, )
        else:
            dcl7 = tester.DCLoad(devices['DCL7'])
            self.dcl = (dcl1, dcl2, dcl3, dcl4, dcl5, dcl6, dcl7, )
        # Relay Drivers
        self.relays = []
        for num in range(1, 23):
            self.relays.append(tester.Relay(devices['RLA{}'.format(num)]))
        # Discharge
        self.discharger = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for ld in self.dcl:
            ld.output(0.0)
        for dcs in self.dcs:
            dcs.output(0.0, False)
        for rla in self.relays:
            rla.set_off()


class Sensors(object):

    """Sensors."""

    def __init__(self, logical_devices, is_ate2):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        # Self Checker Voltages
        self.o12V = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.1)
        self.o5Va = sensor.Vdc(dmm, high=2, low=3, rng=10, res=0.1)
        self.o5Vb = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.1)
        self.o5Vc = sensor.Vdc(dmm, high=4, low=3, rng=10, res=0.1)
        self.o5Vd = sensor.Vdc(dmm, high=15, low=3, rng=10, res=0.1)
        self.o5Ve = sensor.Vdc(dmm, high=16, low=3, rng=10, res=0.1)
        # DSO
        self.oShield1 = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.1)
        self.oShield2 = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.1)
        self.oShield3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.1)
        self.oShield4 = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.1)
        tbase = sensor.Timebase(
            range=0.10, main_mode=True, delay=0, centre_ref=True)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=False, pos_slope=True)
        rdgs = []
        for ch in range(1, 5):
            rdgs.append(sensor.Vavg(ch=ch))
        subchans1 = []
        for ch in range(1, 5):
            subchans1.append(
                sensor.Channel(
                    ch=ch, mux=1, range=40.0,
                    offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan1 = sensor.DSO(dso, subchans1, tbase, trg, rdgs)
        subchans2 = []
        for ch in range(1, 5):
            subchans2.append(
                sensor.Channel(
                    ch=ch, mux=2, range=40.0,
                    offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan2 = sensor.DSO(dso, subchans2, tbase, trg, rdgs)
        subchans3 = []
        for ch in range(1, 5):
            subchans3.append(
                sensor.Channel(
                    ch=ch, mux=3, range=40.0,
                    offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan3 = sensor.DSO(dso, subchans3, tbase, trg, rdgs)
        subchans4 = []
        for ch in range(1, 5):
            subchans4.append(
                sensor.Channel(
                    ch=ch, mux=4, range=40.0,
                    offset=0, dc_coupling=True, att=1, bwlim=True))
        subchan4 = sensor.DSO(dso, subchans4, tbase, trg, rdgs)
        self.subchan = (subchan1, subchan2, subchan3, subchan4)
        # DC Sources
        dcs1 = sensor.Vdc(dmm, high=18, low=8, rng=100, res=0.001)
        dcs2 = sensor.Vdc(dmm, high=19, low=8, rng=100, res=0.001)
        dcs3 = sensor.Vdc(dmm, high=20, low=8, rng=100, res=0.001)
        dcs4 = sensor.Vdc(dmm, high=21, low=8, rng=100, res=0.001)
        dcs5 = sensor.Vdc(dmm, high=22, low=8, rng=100, res=0.001)
        if is_ate2:
            self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5)
        else:
            dcs6 = sensor.Vdc(dmm, high=23, low=8, rng=100, res=0.001)
            dcs7 = sensor.Vdc(dmm, high=24, low=8, rng=100, res=0.001)
            self.dcs = (dcs1, dcs2, dcs3, dcs4, dcs5, dcs6, dcs7)
        # AC Sources
        self.oAcs = sensor.Vac(dmm, high=14, low=4, rng=300, res='MAX')
        # DC Loads
        self.oShunt = sensor.Vdc(
            dmm, high=6, low=2, rng=0.1, res='MAX', scale=1000)
        # Relay Drivers
        self.oRla12V = sensor.Vdc(dmm, high=17, low=1, rng=100, res=0.1)
        self.oRla = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        # Discharge
        self.oDisch1 = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.1)
        self.oDisch2 = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.1)
        self.oDisch3 = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.1)


class Measurements(object):

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        # Self Checker Voltages
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.dmm_5Va = Measurement(limits['5V'], sense.o5Va)
        self.dmm_5Vb = Measurement(limits['5V'], sense.o5Vb)
        self.dmm_5Vc = Measurement(limits['5V'], sense.o5Vc)
        self.dmm_5Vd = Measurement(limits['5V'], sense.o5Vd)
        self.dmm_5Ve = Measurement(limits['5V'], sense.o5Ve)

        # DSO
        self.dmm_shld1off = Measurement(limits['ShieldOFF'], sense.oShield1)
        self.dmm_shld2off = Measurement(limits['ShieldOFF'], sense.oShield2)
        self.dmm_shld3off = Measurement(limits['ShieldOFF'], sense.oShield3)
        self.dmm_shld4off = Measurement(limits['ShieldOFF'], sense.oShield4)
        self.dmm_shld1on = Measurement(limits['ShieldON'], sense.oShield1)
        self.dmm_shld2on = Measurement(limits['ShieldON'], sense.oShield2)
        self.dmm_shld3on = Measurement(limits['ShieldON'], sense.oShield3)
        self.dmm_shld4on = Measurement(limits['ShieldON'], sense.oShield4)

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
        self.dmm_dcs = (
            (5.0, dcs_05), (10.0, dcs_10), (20.0, dcs_20), (35.0, dcs_35))
        # AC Source
        self.dmm_120Vac = Measurement(limits['120Vac'], sense.oAcs)
        self.dmm_240Vac = Measurement(limits['240Vac'], sense.oAcs)
        # DC Loads
        self.dmm_Shunt = (
            (5.0, Measurement(limits['Dcl05'], sense.oShunt)),
            (10.0, Measurement(limits['Dcl10'], sense.oShunt)),
            (20.0, Measurement(limits['Dcl20'], sense.oShunt)),
            (40.0, Measurement(limits['Dcl40'], sense.oShunt)))
        # Relay Drivers
        self.dmm_Rla12V = Measurement(limits['12V'], sense.oRla12V)
        self.dmm_RlaOn = Measurement(limits['RlaOn'], sense.oRla)
        self.dmm_RlaOff = Measurement(limits['RlaOff'], sense.oRla)
        # Discharge
        self.dmm_Disch1On = Measurement(limits['Disch_on'], sense.oDisch1)
        self.dmm_Disch2On = Measurement(limits['Disch_on'], sense.oDisch2)
        self.dmm_Disch3On = Measurement(limits['Disch_on'], sense.oDisch3)
        self.dmm_Disch1Off = Measurement(limits['Disch_off'], sense.oDisch1)
        self.dmm_Disch2Off = Measurement(limits['Disch_off'], sense.oDisch2)
        self.dmm_Disch3Off = Measurement(limits['Disch_off'], sense.oDisch3)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # ACSource:  Apply AC input, measure.
        self.acs = tester.SubStep((
            tester.AcSubStep(
                acs=d.acsource, voltage=120.0, output=True, delay=0.5),
            tester.MeasureSubStep((m.dmm_120Vac, ), timeout=5),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=0.5),
            tester.MeasureSubStep((m.dmm_240Vac, ), timeout=5, delay=0.5),
            ))
        # Checker:  Measure.
        self.check = tester.SubStep((
            tester.MeasureSubStep(
                (m.dmm_12V, m.dmm_5Va, m.dmm_5Vb, m.dmm_5Vc, m.dmm_5Vd,
                m.dmm_5Ve), timeout=5),
            ))
        # DsoShield:  Measure.
        self.shld_off = tester.SubStep((
            tester.MeasureSubStep(
                (m.dmm_shld1off, m.dmm_shld2off, m.dmm_shld3off,
                m.dmm_shld4off, ), timeout=5),
            ))
        self.shld_on = tester.SubStep((
            tester.MeasureSubStep(
                (m.dmm_shld1on, m.dmm_shld2on, m.dmm_shld3on,
                m.dmm_shld4on, ), timeout=5),
            ))
        # Discharge:  Measure on/off.
        self.disch_on = tester.SubStep((
            tester.MeasureSubStep(
                (m.dmm_Disch1On, m.dmm_Disch2On, m.dmm_Disch3On, ),
                timeout=5),
            ))
        self.disch_off = tester.SubStep((
            tester.MeasureSubStep(
                (m.dmm_Disch1Off, m.dmm_Disch2Off, m.dmm_Disch3Off, ),
                timeout=5),
            ))
