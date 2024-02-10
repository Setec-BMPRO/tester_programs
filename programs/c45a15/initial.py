#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""C45A-15 Initial Test Program."""

import serial

import tester

import share
from . import arduino


class Initial(share.TestSequence):

    """C45A-15 Initial Test Program."""

    limitdata = (
        tester.LimitDelta("VacStart", 95.0, 3.0),
        tester.LimitDelta("Vac", 240.0, 5.0),
        tester.LimitDelta("Vbus", 340.0, 10.0),
        tester.LimitBetween("Vcc", 9.5, 15.0),
        tester.LimitDelta("Vref", 5.0, 0.1),
        tester.LimitLow("VrefOff", 1.0),
        tester.LimitDelta("VoutPreExt", 12.0, 0.1),
        tester.LimitDelta("VoutExt", 12.0, 0.1),
        tester.LimitDelta("VoutPre", 12.0, 0.1),
        # PS-5056: Change limit from 9.0V ± 5% to 8.75V ± 5%
        #        tester.LimitBetween('VoutLow', 8.55, 9.45),
        tester.LimitPercent("VoutLow", 8.75, 5),
        tester.LimitBetween("Vout", 15.2, 16.8),
        tester.LimitBetween("VsenseLow", 8.2, 10.0),
        tester.LimitBetween("VsenseOn", 11.8, 12.1),
        tester.LimitLow("VsenseOff", 1.0),
        tester.LimitBetween("GreenOn", 1.8, 2.2),
        tester.LimitBetween("YellowOn", 1.6, 2.2),
        tester.LimitBetween("RedOn", 4.0, 5.5),
        tester.LimitBetween("RedFlash", 2.0, 2.75),
        tester.LimitLow("LedOff", 0.2),
        tester.LimitLow("inOVP", 6.5),
        tester.LimitBetween("OVP", 18.0, 21.0),
        tester.LimitBetween("Reg", -1.5, 0),
        tester.LimitLow("inOCP", 1e6),
        tester.LimitBetween("OCP", 2.85, 3.15),
        tester.LimitLow("FixtureLock", 20),
        tester.LimitInteger("Program", 0),
        tester.LimitRegExp("Reply", "^OK$"),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("FixtureLock", self._step_fixture_lock),
            tester.TestStep("SecCheck", self._step_sec_check),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("OVP", self._step_ovp),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Load", self._step_load),
            tester.TestStep("OCP", self._step_ocp),
        )

    @share.teststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes["dmm_Lock"](timeout=5)

    @share.teststep
    def _step_sec_check(self, dev, mes):
        """Apply external dc to secondary and measure voltages."""
        dev["dcs_Vout"].output(12.0, output=True)
        self.measure(
            (
                "dmm_VoutPreExt",
                "dmm_VsenseOff",
                "dmm_VoutExt",
            ),
            timeout=5,
        )
        dev["dcs_VsecBias"].output(12.0, output=True, delay=1)
        self.measure(
            (
                "dmm_Vref",
                "dmm_VsenseOn",
                "dmm_VoutExt",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the PIC device."""
        dev["rla_Prog"].set_on()
        dev["rla_Prog"].opc()
        mes["pgm_c45a15"]()
        dev["rla_Prog"].set_off()

    @share.teststep
    def _step_ovp(self, dev, mes):
        """Apply external dc and measure output OVP."""
        dev["dcs_VsecBias"].output(0.0, delay=0.5)
        mes["dmm_VrefOff"](timeout=5)
        dev["dcs_VsecBias"].output(12.0)
        mes["dmm_GreenOn"](timeout=5)
        dev["dcs_Vbias"].output(12.0, output=True)
        self.measure(("dmm_Vcc", "ramp_OVP"), timeout=5)
        self.dcsource(
            (("dcs_Vout", 0.0), ("dcs_Vbias", 0.0), ("dcs_VsecBias", 0.0)),
            output=False,
            delay=1,
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit at 95Vac and measure primary voltages."""
        dev["acsource"].output(95.0, output=True, delay=0.5)
        self.measure(
            (
                "dmm_VacStart",
                "dmm_Vcc",
                "dmm_Vref",
                "dmm_GreenOn",
                "dmm_YellowOff",
                "dmm_RedOff",
                "dmm_VoutLow",
                "dmm_VsenseLow",
            ),
            timeout=5,
        )
        dev["acsource"].output(240.0, delay=0.5)
        self.measure(
            (
                "dmm_Vac",
                "dmm_VoutLow",
            ),
            timeout=5,
        )
        dev["rla_CMR"].set_on()
        self.measure(
            (
                "dmm_YellowOn",
                "dmm_Vout",
                "dmm_RedOn",
            ),
            timeout=12,
        )

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure load regulation."""
        dev["dcl"].output(0.0, True)
        dev["rla_Load"].set_on()
        noload = mes["dmm_Vout"](timeout=5).value1
        dev["dcl"].output(3.0)
        fullload = mes["dmm_Vout"](timeout=5).value1
        reg = ((fullload - noload) / noload) * 100
        mes["loadReg"].sensor.store(reg)
        mes["loadReg"]()
        # Calculate the trip point of output voltage for OCP check
        reg = self.limits["Reg"].limit[0]
        triplevel = noload + (noload * (reg / 100))
        self._logger.debug("OCP Trip Level: %s", triplevel)
        self.limits["inOCP"].adjust(triplevel)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes["ramp_OCP"]()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcs_Vout", tester.DCSource, "DCS1"),
            ("dcs_Vbias", tester.DCSource, "DCS2"),
            ("dcs_VsecBias", tester.DCSource, "DCS3"),
            ("dcs_Vcom", tester.DCSource, "DCS4"),
            ("dcl", tester.DCLoad, "DCL1"),
            ("rla_Load", tester.Relay, "RLA1"),
            ("rla_CMR", tester.Relay, "RLA2"),
            ("rla_Prog", tester.Relay, "RLA4"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port("017823", "ARDUINO")
        self["ard"] = arduino.Arduino(ard_ser)
        # Switch on power to fixture circuits
        self["dcs_Vcom"].output(12.0, output=True, delay=2)
        self.add_closer(lambda: self["dcs_Vcom"].output(0.0, output=False))
        self["ard"].open()
        self.add_closer(lambda: self["ard"].close())

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(5.0, delay=1)
        for dcs in ("dcs_Vout", "dcs_Vbias", "dcs_VsecBias"):
            self[dcs].output(0.0, False)
        self["dcl"].output(0.0, False)
        for rla in ("rla_Load", "rla_CMR", "rla_Prog"):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oMirReg"] = sensor.Mirror()
        self["oLock"] = sensor.Res(dmm, high=14, low=6, rng=10000, res=1)
        self["oVac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self["oVbus"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self["oVcc"] = sensor.Vdc(dmm, high=6, low=2, rng=100, res=0.01)
        self["oVref"] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.01)
        self["oVoutPre"] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.01)
        self["oVout"] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.01)
        self["oVsense"] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self["oGreen"] = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.01)
        self["oYellow"] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.01)
        self["oRed"] = sensor.Vdc(dmm, high=12, low=3, rng=10, res=0.01)
        self["oOVP"] = sensor.Ramp(
            stimulus=self.devices["dcs_Vout"],
            sensor=self["oVcc"],
            detect_limit=self.limits["inOVP"],
            ramp_range=sensor.RampRange(start=18.0, stop=22.0, step=0.1),
            delay=0.05,
        )
        self["oOCP"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["oVout"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=1.0, stop=3.2, step=0.03),
            delay=0.1,
        )
        # Arduino sensor
        ard = self.devices["ard"]
        self["pgmC45A15"] = sensor.Keyed(ard, "PGM_C45A15")


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("loadReg", "Reg", "oMirReg", ""),
                ("dmm_Lock", "FixtureLock", "oLock", ""),
                ("dmm_VacStart", "VacStart", "oVac", ""),
                ("dmm_Vac", "Vac", "oVac", ""),
                ("dmm_Vbus", "Vbus", "oVbus", ""),
                ("dmm_Vcc", "Vcc", "oVcc", ""),
                ("dmm_Vref", "Vref", "oVref", ""),
                ("dmm_VrefOff", "VrefOff", "oVref", ""),
                ("dmm_VoutPreExt", "VoutPreExt", "oVoutPre", ""),
                ("dmm_VoutExt", "VoutExt", "oVout", ""),
                ("dmm_VoutPre", "VoutPre", "oVoutPre", ""),
                ("dmm_VoutLow", "VoutLow", "oVout", ""),
                ("dmm_Vout", "Vout", "oVout", ""),
                ("dmm_VsenseLow", "VsenseLow", "oVsense", ""),
                ("dmm_VsenseOn", "VsenseOn", "oVsense", ""),
                ("dmm_VsenseOff", "VsenseOff", "oVsense", ""),
                ("dmm_GreenOn", "GreenOn", "oGreen", ""),
                ("dmm_GreenOff", "LedOff", "oGreen", ""),
                ("dmm_YellowOn", "YellowOn", "oYellow", ""),
                ("dmm_YellowOff", "LedOff", "oYellow", ""),
                ("dmm_RedOn", "RedOn", "oRed", ""),
                ("dmm_RedOff", "LedOff", "oRed", ""),
                ("ramp_OVP", "OVP", "oOVP", ""),
                ("ramp_OCP", "OCP", "oOCP", ""),
                ("pgm_c45a15", "Reply", "pgmC45A15", ""),
            )
        )
