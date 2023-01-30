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
    vin_set = 12.0  # Input DC voltage to power the unit
    vac_set = 220.0 # Input AC voltage
    testlimits = (  # Test limits
        tester.LimitBetween("Vin", vin_set - 1.0, vin_set, doc="Input voltage present"),
        tester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        tester.LimitPercent("AcVoltage", vac_set, 10.0, doc="AC voltage reading"),
        tester.LimitPercent("AcCurrent", 100.0, 10.0, doc="AC current reading"),
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

# FIXME: AC Source 220V, Read & decode CAN traffic


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
        self["canreader"] = tester.CANReader(self["can"])
        self["decoder"] = share.can.PacketPropertyReader(
            self["canreader"], share.can.ACMONStatusPacket
        )

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["canreader"].stop()
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
        self["voltage1"] = sensor.Keyed(self.devices["decoder"], "voltage1")
        self["voltage2"] = sensor.Keyed(self.devices["decoder"], "voltage2")
        self["current1"] = sensor.Keyed(self.devices["decoder"], "current1")
        self["current2"] = sensor.Keyed(self.devices["decoder"], "current2")


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
                ("voltage1", "AcVoltage", "voltage1", "Phase 1 voltage"),
                ("voltage2", "AcVoltage", "voltage2", "Phase 2 voltage"),
                ("current1", "AcCurrent", "current1", "Current sensor 1"),
                ("current2", "AcCurrent", "current2", "Current sensor 2"),
            )
        )
