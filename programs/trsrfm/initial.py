#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""TRS-RFM Initial Program."""

import pathlib

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
        tester.LimitDelta("Vin", vbatt, 0.5, doc="Input voltage present"),
        tester.LimitPercent("3V3", 3.3, 1.5, doc="3V3 present"),
        tester.LimitHigh("LedOff", 3.1, doc="Led off"),
        tester.LimitLow("LedOn", 0.5, doc="Led on"),
        tester.LimitRegExp(
            "ARM-SwVer",
            "^{0}$".format(sw_version.replace(".", r"\.")),
            doc="Software version",
        ),
        tester.LimitRegExp("BleMac", r"^[0-9a-f]{12}$", doc="Valid MAC address"),
        tester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
    )

    def open(self, uut):
        """Prepare for testing."""
        Sensors.sw_image = self.sw_image
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Operation", self._step_operation),
            tester.TestStep("Bluetooth", self._step_bluetooth),
        )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_sernum")
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
        trsrfm.initialise(self.hw_version, self.sernum)
        mes["arm_swver"]()
        trsrfm.override(share.console.parameter.OverrideTo.FORCE_ON)
        self.measure(("dmm_redon", "dmm_greenon", "dmm_blueon"), timeout=5)
        trsrfm.override(share.console.parameter.OverrideTo.FORCE_OFF)
        self.measure(("dmm_redoff", "dmm_greenoff", "dmm_blueoff"), timeout=5)
        trsrfm.override(share.console.parameter.OverrideTo.NORMAL)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test Bluetooth."""
        trsrfm = dev["trsrfm"]
        # Get the MAC address from the console.
        mac = trsrfm.get_mac()
        mes["ble_mac"].sensor.store(mac)
        mes["ble_mac"]()
        dev["rla_pair_btn"].set_on()
        # Scan for the unit
        reply = dev["pi_bt"].scan_advert_blemac(mac, timeout=20)
        mes["scan_mac"].sensor.store(reply is not None)
        mes["scan_mac"]()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        fixture = "034882"
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
        trsrfm_ser.port = share.config.Fixture.port(fixture, "NORDIC")
        self["trsrfm"] = console.Console(trsrfm_ser)
        # Connection to RaspberryPi bluetooth server
        self["pi_bt"] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url()
        )

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
        self["mirmac"] = sensor.Mirror()
        self["mirscan"] = sensor.Mirror()
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_image,
        )
        trsrfm = self.devices["trsrfm"]
        self["arm_SwVer"] = sensor.Keyed(trsrfm, "SW_VER")
        self["sernum"] = sensor.DataEntry(
            message=tester.translate("trsrfm_initial", "msgSnEntry"),
            caption=tester.translate("trsrfm_initial", "capSnEntry"),
        )
        self["sernum"].doc = "Barcode scanner"


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
                ("ble_mac", "BleMac", "mirmac", "Validate MAC address from console"),
                (
                    "scan_mac",
                    "ScanMac",
                    "mirscan",
                    "Validate MAC address over bluetooth",
                ),
                ("arm_swver", "ARM-SwVer", "arm_SwVer", "Unit software version"),
                ("ui_sernum", "SerNum", "sernum", "Unit serial number"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
