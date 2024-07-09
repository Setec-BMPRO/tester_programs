#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""TRS2 Final Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """TRS2 Final Test Program."""

    vbatt = 12.0  # Injected Vbatt
    limitdata = (
        libtester.LimitDelta("Vin", vbatt, 0.5, doc="Input voltage present"),
        libtester.LimitBoolean("ScanSer", True, doc="Serial number detected"),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Bluetooth", self._step_bluetooth),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        dev["dcs_vin"].output(self.vbatt, True)
        mes["dmm_vin"](timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        reply = dev["pi_bt"].scan_beacon_sernum(self.uuts[0].sernum)
        mes["scan_ser"].sensor.store(reply)
        mes["scan_ser"]()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["pi_bt"] = self.physical_devices["BLE"]

    def reset(self):
        """Reset instruments."""
        self["dcs_vin"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self["vin"].doc = "Within Fixture"
        self["mirscan"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                (
                    "scan_ser",
                    "ScanSer",
                    "mirscan",
                    "Scan for serial number over bluetooth",
                ),
            )
        )
