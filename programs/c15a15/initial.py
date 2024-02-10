#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""C15A-15 Initial Test Program."""

import tester

import share


class Initial(share.TestSequence):

    """C15A-15 Initial Test Program."""

    limitdata = (
        tester.LimitBetween("AcMin", 85, 95),
        tester.LimitBetween("VbusMin", 120, 135),
        tester.LimitBetween("VccMin", 7, 14),
        tester.LimitBetween("Ac", 230, 245),
        tester.LimitBetween("Vbus", 330, 350),
        tester.LimitBetween("Vcc", 10, 14),
        tester.LimitHigh("LedOn", 6.5),
        tester.LimitLow("LedOff", 0.5),
        tester.LimitPercent("Vout", 15.5, 2.0),
        tester.LimitBetween("OCP_Range", 0.9, 1.4),
        tester.LimitLow("inOCP", 15.2),
        tester.LimitBetween("OCP", 1.05, 1.35),
        tester.LimitBetween("VoutOcp", 5, 16),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("Power90", self._step_power_90),
            tester.TestStep("Power240", self._step_power_240),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("PowerOff", self._step_power_off),
        )

    @share.teststep
    def _step_power_90(self, dev, mes):
        """Power up at 90Vac."""
        dev["acsource"].output(90.0, output=True, delay=0.5)
        dev["dcl"].output(0.0, output=True)
        self.measure(
            (
                "dmm_vin90",
                "dmm_vbus90",
                "dmm_vcc90",
                "dmm_vout",
                "dmm_green_on",
                "dmm_yellow_off",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_power_240(self, dev, mes):
        """Power up at 240Vac."""
        dev["acsource"].output(240.0, delay=0.5)
        self.measure(
            (
                "dmm_vin",
                "dmm_vbus",
                "dmm_vcc",
                "dmm_vout",
                "dmm_green_on",
                "dmm_yellow_off",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP."""
        dev["dcl"].output(0.9)
        self.measure(
            (
                "dmm_vout",
                "ramp_ocp",
            )
        )
        dev["dcl"].output(0.0)
        with dev["rla_load"]:
            self.measure(
                (
                    "dmm_yellow_on",
                    "dmm_green_on",
                    "dmm_vout_ocp",
                ),
                timeout=5.0,
            )
        mes["dmm_vout"](timeout=2.0)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Input AC off and discharge."""
        dev["dcl"].output(1.0)
        dev["acsource"].output(0.0, output=False, delay=2)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcl", tester.DCLoad, "DCL5"),
            ("rla_load", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(0.0, False)
        self["rla_load"].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self["vbus"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self["vcc"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self["green"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self["yellow"] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self["vout"] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self["ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["vout"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=0.9, stop=1.4, step=0.02),
            delay=0.5,
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin90", "AcMin", "vin", ""),
                ("dmm_vin", "Ac", "vin", ""),
                ("dmm_vbus90", "VbusMin", "vbus", ""),
                ("dmm_vbus", "Vbus", "vbus", ""),
                ("dmm_vcc90", "VccMin", "vcc", ""),
                ("dmm_vcc", "Vcc", "vcc", ""),
                ("dmm_green_on", "LedOn", "green", ""),
                ("dmm_yellow_off", "LedOff", "yellow", ""),
                ("dmm_yellow_on", "LedOn", "yellow", ""),
                ("dmm_vout", "Vout", "vout", ""),
                ("ramp_ocp", "OCP", "ocp", ""),
                ("dmm_vout_ocp", "VoutOcp", "vout", ""),
            )
        )
