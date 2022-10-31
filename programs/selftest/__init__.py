#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd
"""Selfchecker Test Program."""

import tester
import share


class Main(share.TestSequence):

    """Selfchecker Test Program."""

    limitdata = (
        tester.LimitDelta("12V", 12.0, 0.5),
        tester.LimitDelta("5V", 5.0, 0.5),
        tester.LimitBetween("ShieldOFF", -0.5, 7.0),
        tester.LimitBetween("ShieldON", -0.5, 7.0),
        tester.LimitDelta("Dso8", 8.0, 0.5),
        tester.LimitDelta("Dso6", 6.0, 0.5),
        tester.LimitDelta("Dso4", 4.0, 0.5),
        tester.LimitBetween("Dso2", 1.35, 2.5),
        tester.LimitDelta("Dcs5", 5.0, 0.5),
        tester.LimitDelta("Dcs10", 10.0, 0.5),
        tester.LimitDelta("Dcs20", 20.0, 0.5),
        tester.LimitDelta("Dcs35", 35.0, 0.5),
        tester.LimitDelta("120Vac", 120.0, 5.0),
        tester.LimitDelta("240Vac", 240.0, 5.0),
        tester.LimitDelta("Dcl05", 5.0, 1),
        tester.LimitDelta("Dcl10", 10.0, 1),
        tester.LimitDelta("Dcl20", 20.0, 1),
        tester.LimitDelta("Dcl40", 40.0, 1),
        tester.LimitDelta("RlaOff", 12.0, 0.5),
        tester.LimitLow("RlaOn", 1.5),
        tester.LimitDelta("Disch_on", 10.0, 1.0),
        tester.LimitLow("Disch_off", 0.5),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        is_ate2 = share.config.System.tester_type.startswith("ATE2")
        Devices.is_ate2 = is_ate2
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("ACSource", self._step_acsource),
            tester.TestStep("Checker", self._step_checker),
            tester.TestStep("DSO", self._step_dso, not is_ate2),
            tester.TestStep("DCSource", self._step_dcsource),
            tester.TestStep("DCLoad", self._step_dcload),
            tester.TestStep("RelayDriver", self._step_relaydriver),
            tester.TestStep("Discharge", self._step_discharge),
        )

    @share.teststep
    def _step_acsource(self, dev, mes):
        """Apply AC inputs to Fixture and measure ac voltages."""
        acs = dev["acsource"]
        acs.configure(ocp="MAX", rng=300)
        acs.output(120.0, output=True, delay=0.5)
        mes["dmm_120Vac"](timeout=5)
        acs.output(240.0, output=True, delay=0.5)
        mes["dmm_240Vac"](timeout=5)

    @share.teststep
    def _step_checker(self, dev, mes):
        """With 240Vac input applied, measure Fixture dc voltages."""
        self.measure(
            (
                "dmm_12V",
                "dmm_5Va",
                "dmm_5Vb",
                "dmm_5Vc",
                "dmm_5Vd",
                "dmm_5Ve",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_dso(self, dev, mes):
        """Test DSO.

        Measure all DSO input connector shields off.
        The 4 channels are connected to 8V, 6V, 4V, 2V from the Fixture.
        For each subchannel in turn, measure voltages on all 4 inputs and
        measure all shields on.

        """
        self.measure(
            (
                "dmm_shld1off",
                "dmm_shld2off",
                "dmm_shld3off",
                "dmm_shld4off",
            ),
            timeout=5,
        )
        for meas in mes["dso_subchan"]:
            meas(timeout=5.0)
            self.measure(
                (
                    "dmm_shld1on",
                    "dmm_shld2on",
                    "dmm_shld3on",
                    "dmm_shld4on",
                ),
                timeout=5,
            )

    @share.teststep
    def _step_dcsource(self, dev, mes):
        """Test DC Sources.

        Set all DC Sources together in the steps 5V, 10V, 20V, 35V
        After each step measure voltages on all DC Sources.

        """
        for step, group in mes["dmm_dcs"]:
            for src in dev["dcs"]:
                src.output(voltage=step, output=True)
                src.opc()
            tester.MeasureGroup(group)

    @share.teststep
    def _step_dcload(self, dev, mes):
        """Test DC Loads.

        All DC Loads are connected via a 1mR shunt to the Fixture 5V/50A PSU.
        Set each DC Load in turn to 5A, 10A, 20A, 40A and measure the
        actual current through the shunt for the DC Load.

        """
        for load in dev["dcl"]:
            for current, meas in mes["dmm_Shunt"]:
                load.output(current=current, output=True)
                load.opc()
                meas(timeout=5.0)
            load.output(current=0.0, output=False)

    @share.teststep
    def _step_relaydriver(self, dev, mes):
        """Test Relay Drivers.

        Measure Relay Driver 12V supply.
        Switch on/off each Relay Driver in turn and measure.

        """
        mes["dmm_Rla12V"](timeout=1.0)
        for rly in dev["relays"]:
            with rly:
                mes["dmm_RlaOn"](timeout=5.0)
            mes["dmm_RlaOff"](timeout=5.0)

    @share.teststep
    def _step_discharge(self, dev, mes):
        """Test Discharge.

        Switch Discharger on/off and measure.

        """
        dis = dev["discharger"]
        dis.set_on()
        dis.opc()
        self.measure(
            (
                "dmm_Disch1On",
                "dmm_Disch2On",
                "dmm_Disch3On",
            ),
            timeout=5,
        )
        dis.set_off()
        dis.opc()
        self.measure(
            (
                "dmm_Disch1Off",
                "dmm_Disch2Off",
                "dmm_Disch3Off",
            ),
            timeout=5,
        )


class Devices(share.Devices):

    """Devices."""

    # True if the tester is an ATE2
    is_ate2 = False

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dso", tester.DSO, "DSO"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharger", tester.Discharge, "DIS"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # DC Sources
        self["dcs"] = [
            tester.DCSource(self.physical_devices["DCS1"]),
            tester.DCSource(self.physical_devices["DCS2"]),
            tester.DCSource(self.physical_devices["DCS3"]),
            tester.DCSource(self.physical_devices["DCS4"]),
            tester.DCSource(self.physical_devices["DCS5"]),
        ]
        if not self.is_ate2:
            self["dcs"].extend(
                [
                    tester.DCSource(self.physical_devices["DCS6"]),
                    tester.DCSource(self.physical_devices["DCS7"]),
                ]
            )
        # DC Loads
        self["dcl"] = [
            tester.DCLoad(self.physical_devices["DCL1"]),
            tester.DCLoad(self.physical_devices["DCL2"]),
            tester.DCLoad(self.physical_devices["DCL3"]),
            tester.DCLoad(self.physical_devices["DCL4"]),
            tester.DCLoad(self.physical_devices["DCL5"]),
            tester.DCLoad(self.physical_devices["DCL6"]),
        ]
        if not self.is_ate2:
            self["dcl"].extend(
                [
                    tester.DCLoad(self.physical_devices["DCL7"]),
                ]
            )
        # Relay Drivers
        self["relays"] = []
        for num in range(1, 23):
            self["relays"].append(
                tester.Relay(self.physical_devices["RLA{0}".format(num)])
            )

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        for ld in self["dcl"]:
            ld.output(0.0, False)
        for dcs in self["dcs"]:
            dcs.output(0.0, False)
        for rla in self["relays"]:
            rla.set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        dso = self.devices["dso"]
        sensor = tester.sensor
        # Self Checker Voltages
        self["o12V"] = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.1)
        self["o5Va"] = sensor.Vdc(dmm, high=2, low=3, rng=10, res=0.1)
        self["o5Vb"] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.1)
        self["o5Vc"] = sensor.Vdc(dmm, high=4, low=3, rng=10, res=0.1)
        self["o5Vd"] = sensor.Vdc(dmm, high=15, low=3, rng=10, res=0.1)
        self["o5Ve"] = sensor.Vdc(dmm, high=16, low=3, rng=10, res=0.1)
        # DSO Shields
        self["oShield1"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.1)
        self["oShield2"] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.1)
        self["oShield3"] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.1)
        self["oShield4"] = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.1)
        # AC Sources
        self["oAcs"] = sensor.Vac(dmm, high=14, low=4, rng=300, res="MAX")
        # DC Loads
        self["oShunt"] = sensor.Vdc(dmm, high=6, low=2, rng=0.1, res="MAX", scale=1000)
        # Relay Drivers
        self["oRla12V"] = sensor.Vdc(dmm, high=17, low=1, rng=100, res=0.1)
        self["oRla"] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        # Discharge
        self["oDisch1"] = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.1)
        self["oDisch2"] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.1)
        self["oDisch3"] = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.1)
        # DSO
        tbase = sensor.Timebase(range=0.10, main_mode=True, delay=0, centre_ref=True)
        trg = sensor.Trigger(ch=1, level=1.0, normal_mode=False, pos_slope=True)
        rdgs = []
        for ch in range(1, 5):
            rdgs.append(sensor.Vavg(ch=ch))
        subchans1 = []
        for ch in range(1, 5):
            subchans1.append(
                sensor.Channel(
                    ch=ch,
                    mux=1,
                    range=40.0,
                    offset=0,
                    dc_coupling=True,
                    att=1,
                    bwlim=True,
                )
            )
        subchan1 = sensor.DSO(dso, subchans1, tbase, trg, rdgs)
        subchans2 = []
        for ch in range(1, 5):
            subchans2.append(
                sensor.Channel(
                    ch=ch,
                    mux=2,
                    range=40.0,
                    offset=0,
                    dc_coupling=True,
                    att=1,
                    bwlim=True,
                )
            )
        subchan2 = sensor.DSO(dso, subchans2, tbase, trg, rdgs)
        subchans3 = []
        for ch in range(1, 5):
            subchans3.append(
                sensor.Channel(
                    ch=ch,
                    mux=3,
                    range=40.0,
                    offset=0,
                    dc_coupling=True,
                    att=1,
                    bwlim=True,
                )
            )
        subchan3 = sensor.DSO(dso, subchans3, tbase, trg, rdgs)
        subchans4 = []
        for ch in range(1, 5):
            subchans4.append(
                sensor.Channel(
                    ch=ch,
                    mux=4,
                    range=40.0,
                    offset=0,
                    dc_coupling=True,
                    att=1,
                    bwlim=True,
                )
            )
        subchan4 = sensor.DSO(dso, subchans4, tbase, trg, rdgs)
        self["subchan"] = (
            subchan1,
            subchan2,
            subchan3,
            subchan4,
        )
        # DC Sources
        self["dcs"] = [
            sensor.Vdc(dmm, high=18, low=8, rng=100, res=0.001),
            sensor.Vdc(dmm, high=19, low=8, rng=100, res=0.001),
            sensor.Vdc(dmm, high=20, low=8, rng=100, res=0.001),
            sensor.Vdc(dmm, high=21, low=8, rng=100, res=0.001),
            sensor.Vdc(dmm, high=22, low=8, rng=100, res=0.001),
        ]
        if not self.devices.is_ate2:
            self["dcs"].extend(
                [
                    sensor.Vdc(dmm, high=23, low=8, rng=100, res=0.001),
                    sensor.Vdc(dmm, high=24, low=8, rng=100, res=0.001),
                ]
            )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                # Self Checker Voltages
                ("dmm_12V", "12V", "o12V", ""),
                ("dmm_5Va", "5V", "o5Va", ""),
                ("dmm_5Vb", "5V", "o5Vb", ""),
                ("dmm_5Vc", "5V", "o5Vc", ""),
                ("dmm_5Vd", "5V", "o5Vd", ""),
                ("dmm_5Ve", "5V", "o5Ve", ""),
                # DSO
                ("dmm_shld1off", "ShieldOFF", "oShield1", ""),
                ("dmm_shld2off", "ShieldOFF", "oShield2", ""),
                ("dmm_shld3off", "ShieldOFF", "oShield3", ""),
                ("dmm_shld4off", "ShieldOFF", "oShield4", ""),
                ("dmm_shld1on", "ShieldON", "oShield1", ""),
                ("dmm_shld2on", "ShieldON", "oShield2", ""),
                ("dmm_shld3on", "ShieldON", "oShield3", ""),
                ("dmm_shld4on", "ShieldON", "oShield4", ""),
                # AC Source
                ("dmm_120Vac", "120Vac", "oAcs", ""),
                ("dmm_240Vac", "240Vac", "oAcs", ""),
                # Relay Drivers
                ("dmm_Rla12V", "12V", "oRla12V", ""),
                ("dmm_RlaOn", "RlaOn", "oRla", ""),
                ("dmm_RlaOff", "RlaOff", "oRla", ""),
                # Discharge
                ("dmm_Disch1On", "Disch_on", "oDisch1", ""),
                ("dmm_Disch2On", "Disch_on", "oDisch2", ""),
                ("dmm_Disch3On", "Disch_on", "oDisch3", ""),
                ("dmm_Disch1Off", "Disch_off", "oDisch1", ""),
                ("dmm_Disch2Off", "Disch_off", "oDisch2", ""),
                ("dmm_Disch3Off", "Disch_off", "oDisch3", ""),
            )
        )
        Measurement = tester.Measurement
        # DSO
        self["dso_subchan"] = []
        lims = (
            self.limits["Dso8"],
            self.limits["Dso6"],
            self.limits["Dso4"],
            self.limits["Dso2"],
        )
        for sen in self.sensors["subchan"]:
            self["dso_subchan"].append(Measurement(lims, sen))
        # DC Sources
        dcs_05 = []
        dcs_10 = []
        dcs_20 = []
        dcs_35 = []
        for sen in self.sensors["dcs"]:
            dcs_05.append(Measurement(self.limits["Dcs5"], sen))
            dcs_10.append(Measurement(self.limits["Dcs10"], sen))
            dcs_20.append(Measurement(self.limits["Dcs20"], sen))
            dcs_35.append(Measurement(self.limits["Dcs35"], sen))
        self["dmm_dcs"] = (
            (5.0, dcs_05),
            (10.0, dcs_10),
            (20.0, dcs_20),
            (35.0, dcs_35),
        )
        # DC Loads
        shunt = self.sensors["oShunt"]
        self["dmm_Shunt"] = (
            (5.0, Measurement(self.limits["Dcl05"], shunt)),
            (10.0, Measurement(self.limits["Dcl10"], shunt)),
            (20.0, Measurement(self.limits["Dcl20"], shunt)),
            (40.0, Measurement(self.limits["Dcl40"], shunt)),
        )
