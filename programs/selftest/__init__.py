#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program."""

import tester
from tester.testlimit import lim_hilo_delta, lim_hilo, lim_lo

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('12V', 12.0, 0.5),
    lim_hilo_delta('5V', 5.0, 0.5),
    lim_hilo_delta('ShieldOFF', 6.0, 0.5),
    lim_hilo_delta('ShieldON', 0.0, 0.5),
    lim_hilo_delta('Dso8', 8.0, 0.5),
    lim_hilo_delta('Dso6', 6.0, 0.5),
    lim_hilo_delta('Dso4', 4.0, 0.5),
    lim_hilo('Dso2', 1.35, 2.5),
    lim_hilo_delta('Dcs5', 5.0, 0.5),
    lim_hilo_delta('Dcs10', 10.0, 0.5),
    lim_hilo_delta('Dcs20', 20.0, 0.5),
    lim_hilo_delta('Dcs35', 35.0, 0.5),
    lim_hilo_delta('120Vac', 120.0, 5.0),
    lim_hilo_delta('240Vac', 240.0, 5.0),
    lim_hilo_delta('Dcl05', 5.0, 1),
    lim_hilo_delta('Dcl10', 10.0, 1),
    lim_hilo_delta('Dcl20', 20.0, 1),
    lim_hilo_delta('Dcl40', 40.0, 1),
    lim_hilo_delta('RlaOff', 12.0, 0.5),
    lim_lo('RlaOn', 1.5),
    lim_hilo_delta('Disch_on', 10.0, 1.0),
    lim_lo('Disch_off', 0.5),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Main(tester.testsequence.TestSequence):

    """Selfchecker Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        # True if running on ATE2 tester
        self._is_ate2 = (self.physical_devices.tester_type[:4] == 'ATE2')
        self.steps = (
            tester.TestStep('ACSource', self._step_acsource),
            tester.TestStep('Checker', self._step_checker),
            tester.TestStep('DSO', self._step_dso, not self._is_ate2),
            tester.TestStep('DCSource', self._step_dcsource),
            tester.TestStep('DCLoad', self._step_dcload),
            tester.TestStep('RelayDriver', self._step_relaydriver),
            tester.TestStep('Discharge', self._step_discharge),
            )
        self._limits = LIMITS
        global d, s, m, t
        d = LogicalDevices(self.physical_devices, self._is_ate2)
        s = Sensors(d, self._is_ate2)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_acsource(self):
        """Apply AC inputs to Fixture and measure ac voltages."""
        self.fifo_push(((s.oAcs, (120, 240)), ))
        d.acsource.configure(ocp='MAX', rng=300)
        t.acs.run()

    def _step_checker(self):
        """With 240Vac input applied, measure Fixture dc voltages."""
        self.fifo_push(
            ((s.o12V, 12.0), (s.o5Va, 5.0), (s.o5Vb, 5.0), (s.o5Vc, 5.0),
             (s.o5Vd, 5.0), (s.o5Ve, 5.0), ))
        t.check.run()

    def _step_dso(self):
        """Test DSO.

        Measure all DSO input connector shields off.
        The 4 channels are connected to 8V, 6V, 4V, 2V from the Fixture.
        For each subchannel in turn, measure voltages on all 4 inputs and
        measure all shields on.

        """
        self.fifo_push(((s.oShield1, 6.0), (s.oShield2, 6.0),
                (s.oShield3, 6.0), (s.oShield4, 6.0), ))
        if self.fifo:
            for subch in s.subchan:
                subch.store(((8.0, 6.0, 4.0, 2.0),))
                self.fifo_push(((s.oShield1, 0.0), (s.oShield2, 0.0),
                        (s.oShield3, 0.0), (s.oShield4, 0.0), ))
        t.shld_off.run()
        for meas in m.dso_subchan:
            meas.measure(timeout=5.0)
            t.shld_on.run()

    def _step_dcsource(self):
        """Test DC Sources.

        Set all DC Sources together in the steps 5V, 10V, 20V, 35V
        After each step measure voltages on all DC Sources.

        """
        if self.fifo:
            for src in s.dcs:
                src.store((5.0, 10.0, 20.0, 35.0))
        for step, group in m.dmm_dcs:
            for src in d.dcs:
                src.output(voltage=step, output=True)
                src.opc()
            tester.MeasureGroup(group)

    def _step_dcload(self):
        """Test DC Loads.

        All DC Loads are connected via a 1mR shunt to the Fixture 5V/50A PSU.
        Set each DC Load in turn to 5A, 10A, 20A, 40A and measure the
        actual current through the shunt for the DC Load.

        """
        self.fifo_push(
            ((s.oShunt, (5e-3, 10e-3, 20e-3, 40e-3) * 7), ))
        for load in d.dcl:
            for current, meas in m.dmm_Shunt:
                load.output(current=current, output=True)
                load.opc()
                meas.measure(timeout=5.0)
            load.output(current=0.0, output=False)

    def _step_relaydriver(self):
        """Test Relay Drivers.

        Measure Relay Driver 12V supply.
        Switch on/off each Relay Driver in turn and measure.

        """
        self.fifo_push(
            ((s.oRla12V, 12.0), (s.oRla, (0.5, 12.0) * 22), ))
        m.dmm_Rla12V.measure(timeout=1.0)
        for rly in d.relays:
            rly.set_on()
            rly.opc()
            m.dmm_RlaOn.measure(timeout=5.0)
            rly.set_off()
            rly.opc()
            m.dmm_RlaOff.measure(timeout=5.0)

    def _step_discharge(self):
        """Test Discharge.

        Switch Discharger on/off and measure.

        """
        self.fifo_push(((s.oDisch1, (10.0, 0.0)), (s.oDisch2, (10.0, 0.0)),
                        (s.oDisch3, (10.0, 0.0)), ))
        d.discharger.set_on()
        d.discharger.opc()
        t.disch_on.run()
        d.discharger.set_off()
        d.discharger.opc()
        t.disch_off.run()


class LogicalDevices():

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
        self.acsource.reset()
        for ld in self.dcl:
            ld.output(0.0)
        for dcs in self.dcs:
            dcs.output(0.0, False)
        for rla in self.relays:
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, is_ate2):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        sensor = tester.sensor
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


class Measurements():

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
