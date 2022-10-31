#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 Aux Initial Test Program."""

import tester

import share


class InitialAux(share.TestSequence):

    """IDS-500 Initial Aux Test Program."""

    # Test limits
    limitdata = (
        tester.LimitBetween("5V", 4.90, 5.10),
        tester.LimitLow("5VOff", 0.5),
        tester.LimitLow("15VpOff", 0.5),
        tester.LimitBetween("15Vp", 14.25, 15.75),
        tester.LimitLow("15VpSwOff", 0.5),
        tester.LimitBetween("15VpSw", 14.25, 15.75),
        tester.LimitBetween("20VL", 18.0, 25.0),
        tester.LimitBetween("-20V", -25.0, -18.0),
        tester.LimitBetween("15V", 14.25, 15.75),
        tester.LimitBetween("-15V", -15.75, -14.25),
        tester.LimitLow("PwrGoodOff", 0.5),
        tester.LimitBetween("PwrGood", 4.8, 5.1),
        tester.LimitBetween("ACurr_5V_1", -0.1, 0.1),
        tester.LimitBetween("ACurr_5V_2", 1.76, 2.15),
        tester.LimitBetween("ACurr_15V_1", -0.1, 0.13),
        tester.LimitBetween("ACurr_15V_2", 1.16, 1.42),
        tester.LimitBetween("AuxTemp", 2.1, 4.3),
        tester.LimitLow("InOCP5V", 4.8),
        tester.LimitLow("InOCP15Vp", 14.2),
        tester.LimitBetween("OCP", 7.0, 10.0),
        tester.LimitLow("FixtureLock", 20),
    )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_pwrup),
            tester.TestStep("KeySwitch", self._step_key_switch),
            tester.TestStep("ACurrent", self._step_acurrent),
            tester.TestStep("OCP", self._step_ocp),
        )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power up internal IDS-500 for 20VL, -20V rails."""
        mes["dmm_lock"](timeout=5)
        dev["dcs_fan"].output(12.0, output=True)
        dev["acsource"].output(voltage=240.0, output=True, delay=3.0)
        self.measure(
            (
                "dmm_20VL",
                "dmm__20V",
                "dmm_5Voff",
                "dmm_15V",
                "dmm__15V",
                "dmm_15Vpoff",
                "dmm_15Vpswoff",
                "dmm_pwrgoodoff",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_key_switch(self, dev, mes):
        """Apply 5V to ENABLE_Aux, ENABLE +15VPSW and measure voltages."""
        dev["dcs_5Vfix"].output(5.0, output=True)
        dev["rla_enAux"].set_on()
        self.measure(
            (
                "dmm_5V",
                "dmm_15V",
                "dmm__15V",
                "dmm_15Vp",
                "dmm_15Vpswoff",
                "dmm_pwrgood",
            ),
            timeout=5,
        )
        dev["rla_en15Vpsw"].set_on()
        mes["dmm_15Vpsw"](timeout=5)

    @share.teststep
    def _step_acurrent(self, dev, mes):
        """Test ACurrent: No load, 5V load, 5V load + 15Vp load"""
        self.dcload(
            (
                ("dcl_5V", 0.0),
                ("dcl_15Vp", 0.0),
            )
        )
        self.measure(
            (
                "dmm_ac5V_1",
                "dmm_ac15V_1",
            ),
            timeout=5,
        )
        dev["dcl_5V"].output(6.0)
        self.measure(
            (
                "dmm_ac5V_2",
                "dmm_ac15V_1",
            ),
            timeout=5,
        )
        dev["dcl_15Vp"].output(4.0)
        self.measure(
            (
                "dmm_ac5V_2",
                "dmm_ac15V_2",
            ),
            timeout=5,
        )
        self.dcload(
            (
                ("dcl_5V", 0.0),
                ("dcl_15Vp", 0.0),
            )
        )

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP and voltage a/c R657 with 5V applied via a 100k."""
        self.measure(
            (
                "dmm_5V",
                "ramp_OCP5V",
            ),
            timeout=5,
        )
        dev["dcl_5V"].output(0.0, output=False)
        dev["rla_enAux"].set_off(delay=1)
        dev["rla_enAux"].set_on()
        self.measure(
            (
                "dmm_15Vp",
                "ramp_OCP15Vp",
                "dmm_auxtemp",
            ),
            timeout=5,
        )


class Devices(share.Devices):

    """Aux Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_5Vfix", tester.DCSource, "DCS1"),
            ("dcs_fan", tester.DCSource, "DCS5"),
            ("dcl_5V", tester.DCLoad, "DCL1"),
            ("dcl_15Vp", tester.DCLoad, "DCL2"),
            ("rla_enAux", tester.Relay, "RLA1"),
            ("rla_en15Vpsw", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset(delay=2)
        self["discharge"].pulse()
        for dcs in (
            "dcs_5Vfix",
            "dcs_fan",
        ):
            self[dcs].output(0.0, False)
        for dcl in (
            "dcl_5V",
            "dcl_15Vp",
        ):
            self[dcl].output(0.0, False)
        for rla in (
            "rla_enAux",
            "rla_en15Vpsw",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Aux Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["olock"] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self["o5V"] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self["o15V"] = sensor.Vdc(dmm, high=23, low=1, rng=100, res=0.001)
        self["o_15V"] = sensor.Vdc(dmm, high=22, low=1, rng=100, res=0.001)
        self["o15Vp"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self["o20VL"] = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self["o_20V"] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self["o15VpSw"] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.001)
        self["oACurr5V"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self["oACurr15V"] = sensor.Vdc(dmm, high=16, low=1, rng=10, res=0.001)
        self["oAuxTemp"] = sensor.Vdc(dmm, high=17, low=1, rng=10, res=0.001)
        self["oPwrGood"] = sensor.Vdc(dmm, high=18, low=1, rng=10, res=0.001)
        self["oOCP5V"] = sensor.Ramp(
            stimulus=self.devices["dcl_5V"],
            sensor=self["o5V"],
            detect_limit=self.limits["InOCP5V"],
            ramp_range=sensor.RampRange(start=6.0, stop=11.0, step=0.1),
            delay=0.1,
        )
        self["oOCP15Vp"] = sensor.Ramp(
            stimulus=self.devices["dcl_15Vp"],
            sensor=self["o15Vp"],
            detect_limit=self.limits["InOCP15Vp"],
            ramp_range=sensor.RampRange(start=6.0, stop=11.0, step=0.1),
            delay=0.1,
        )


class Measurements(share.Measurements):

    """Aux Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "olock", ""),
                ("dmm_5Voff", "5VOff", "o5V", ""),
                ("dmm_5V", "5V", "o5V", ""),
                ("dmm_15Vpoff", "15VpOff", "o15Vp", ""),
                ("dmm_15Vp", "15Vp", "o15Vp", ""),
                ("dmm_15Vpswoff", "15VpSwOff", "o15VpSw", ""),
                ("dmm_15Vpsw", "15VpSw", "o15VpSw", ""),
                ("dmm_20VL", "20VL", "o20VL", ""),
                ("dmm__20V", "-20V", "o_20V", ""),
                ("dmm_15V", "15V", "o15V", ""),
                ("dmm__15V", "-15V", "o_15V", ""),
                ("dmm_pwrgoodoff", "PwrGoodOff", "oPwrGood", ""),
                ("dmm_pwrgood", "PwrGood", "oPwrGood", ""),
                ("dmm_ac5V_1", "ACurr_5V_1", "oACurr5V", ""),
                ("dmm_ac5V_2", "ACurr_5V_2", "oACurr5V", ""),
                ("dmm_ac15V_1", "ACurr_15V_1", "oACurr15V", ""),
                ("dmm_ac15V_2", "ACurr_15V_2", "oACurr15V", ""),
                ("dmm_auxtemp", "AuxTemp", "oAuxTemp", ""),
                ("ramp_OCP5V", "OCP", "oOCP5V", ""),
                ("ramp_OCP15Vp", "OCP", "oOCP15Vp", ""),
            )
        )
