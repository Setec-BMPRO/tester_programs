#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Final Program."""

import libtester
import tester

import share
from . import config


class Final(share.TestSequence):
    """MB3 Final Test Program."""

    limitdata = (
        libtester.LimitDelta("Vaux", config.vaux, 0.5),
        libtester.LimitDelta("Vsolar", config.vsol, 0.5),
        libtester.LimitDelta("Vbat", 14.6, 0.3),
        libtester.LimitLow("Vbatoff", 0.5),
        libtester.LimitHigh("Vchem", 2.0, doc="Voltage present on sense conn"),
    )

    def open(self):
        """Create the test program as a linear sequence."""
        super().configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerOn", self._step_power_on),
            tester.TestStep("Solar", self._step_solar),
        )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply Aux input power and measure output."""
        dev["rla_select"].aux()
        dev["dcs_vin"].output(config.vaux, True, delay=0.5)
        self.measure(("dmm_vaux", "dmm_vbat", "dmm_vchem"), timeout=5)

    @share.teststep
    def _step_solar(self, dev, mes):
        """Remove Aux input, apply Solar input power and measure output."""
        dev["rla_select"].solar()
        dev["dcs_vin"].output(config.vsol, delay=0.5)
        self.measure(("dmm_vsol", "dmm_vbatoff"), timeout=5)
        dev["rla_batt"].set_on()
        mes["dmm_vbat"](timeout=5)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("rla_select", tester.Relay, "RLA1"),
            ("rla_batt", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        sel = self["rla_select"]
        sel.aux = sel.set_off
        sel.solar = sel.set_on

    def reset(self):
        """Reset instruments."""
        self["dcs_vin"].output(0.0, False)
        for rla in (
            "rla_select",
            "rla_batt",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vaux"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self["vbat"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self["vchem"] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.01)
        self["vchem"].doc = "X5, pin1"
        self["vsol"] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vaux", "Vaux", "vaux", "Aux input ok"),
                ("dmm_vbat", "Vbat", "vbat", "Battery output ok"),
                ("dmm_vbatoff", "Vbatoff", "vbat", "No output"),
                ("dmm_vchem", "Vchem", "vchem", "Sense connector plugged in"),
                ("dmm_vsol", "Vsolar", "vsol", "Solar input ok"),
            )
        )
