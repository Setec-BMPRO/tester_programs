#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""TRS-RFM Initial Program."""

import pathlib

import libtester
import serial
import tester

import share

from . import console


class Initial(share.TestSequence):
    """TRS-RFM Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    sw_version = "1.0.19844.2444"
    sw_image = "trs-rfm_factory_{0}.hex".format(sw_version)
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_version = (5, 0, "A")
    # Test limits
    limitdata = (
        libtester.LimitDelta("Vin", vbatt, 0.5, doc="Input voltage present"),
        libtester.LimitPercent("3V3", 3.3, 1.5, doc="3V3 present"),
        libtester.LimitHigh("LedOff", 3.1, doc="Led off"),
        libtester.LimitLow("LedOn", 0.5, doc="Led on"),
        libtester.LimitRegExp(
            "ARM-SwVer",
            r"^{0}$".format(sw_version.replace(".", r"\.")),
            doc="Software version",
        ),
        libtester.LimitRegExp("BleMac", share.MAC.regex, doc="Valid MAC address"),
        libtester.LimitHigh("ScanRSSI", -90, doc="Strong BLE signal"),
    )

    def open(self):
        """Prepare for testing."""
        Sensors.sw_image = self.sw_image
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Operation", self._step_operation),
            tester.TestStep("Bluetooth", self._step_bluetooth),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        dev["dcs_vin"].output(self.vbatt, True)
        self.measure(
            (
                "dmm_vin",
                "dmm_3v3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program both devices."""
        mes["JLink"]()

    @share.teststep
    def _step_operation(self, dev, mes):
        """Test the operation of TRSRFM."""
        trsrfm = dev["trsrfm"]
        trsrfm.open()
        trsrfm.initialise(self.hw_version, self.uuts[0].sernum)
        mes["arm_swver"]()
        trsrfm.override(share.console.parameter.OverrideTo.FORCE_ON)
        self.measure(("dmm_redon", "dmm_greenon", "dmm_blueon"), timeout=5)
        trsrfm.override(share.console.parameter.OverrideTo.FORCE_OFF)
        self.measure(("dmm_redoff", "dmm_greenoff", "dmm_blueoff"), timeout=5)
        trsrfm.override(share.console.parameter.OverrideTo.NORMAL)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test Bluetooth."""
        mac = mes["ble_mac"]().value1
        dev["rla_pair_btn"].set_on()
        # Scan for the unit
        dev["BLE"].uut = self.uuts[0]
        dev["BLE"].mac = mac
        mes["rssi"]()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS1"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_pair_btn", tester.Relay, "RLA8"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        trsrfm_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        trsrfm_ser.port = self.port("NORDIC")
        self["trsrfm"] = console.Console(trsrfm_ser)

    def reset(self):
        """Reset instruments."""
        self["trsrfm"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_reset", "rla_pair_btn"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "Across X1-X2"
        self["3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3v3"].doc = "U2 output"
        self["red"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self["red"].doc = "Led cathode"
        self["green"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self["green"].doc = "Led cathode"
        self["blue"] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self["blue"].doc = "Led cathode"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_image,
        )
        trsrfm = self.devices["trsrfm"]
        self["arm_SwVer"] = sensor.Keyed(trsrfm, "SW_VER")
        self["BleMac"] = sensor.Keyed(trsrfm, "BT_MAC")
        self["BleMac"].on_read = lambda value: value.replace(":", "").lower()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("dmm_redoff", "LedOff", "red", "Red led off"),
                ("dmm_redon", "LedOn", "red", "Red led on"),
                ("dmm_greenoff", "LedOff", "green", "Green led off"),
                ("dmm_greenon", "LedOn", "green", "Green led on"),
                ("dmm_blueoff", "LedOff", "blue", "Blue led off"),
                ("dmm_blueon", "LedOn", "blue", "Blue led on"),
                ("ble_mac", "BleMac", "BleMac", "Validate MAC address from console"),
                ("rssi", "ScanRSSI", "RSSI", "Bluetooth RSSI Level"),
                ("arm_swver", "ARM-SwVer", "arm_SwVer", "Unit software version"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
