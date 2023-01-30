#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Initial Test Program."""

import pathlib

import tester

import share


class Initial(share.TestSequence):

    """RVMD50 Initial Test Program."""

    sw_image = "no_sw_available_yet.bin"
    vin_set = 12.0  # Input voltage to power the unit
    testlimits = (  # Test limits
        tester.LimitBetween("Vin", vin_set - 1.0, vin_set, doc="Input voltage present"),
        tester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
    )

    def open(self, uut):
        """Prepare for testing."""
        Sensors.sw_image = self.sw_image
        super().open(self.testlimits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Run", self._step_run),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        dev["dcs_vin"].output(self.vin_set, output=True)
        self.measure(("dmm_vin", "dmm_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        mes["JLink"]()

    @share.teststep
    def _step_run(self, dev, mes):
        """Run the unit."""
        # TODO: AC Source 220V, Read & decode CAN traffic


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acs", tester.ACSource, "ACS"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["can"] = self.physical_devices["_CAN"]

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True

    def reset(self):
        """Test run has stopped."""
        self["can"].rvc_mode = False
        self["acs"].output(0.0, False)
        self["dcs_vin"].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    projectfile = "acmon_XXXX.jflash"
    sw_image = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "X1"
        self["3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3v3"].doc = "U1 output"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            pathlib.Path(__file__).parent / self.projectfile,
            pathlib.Path(__file__).parent / self.sw_image,
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
