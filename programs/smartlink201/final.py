#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """SmartLink201 Final Test Program."""

    limitdata = (
        libtester.LimitHigh(
            "ScanRSSI",
            (
                -70
                if share.config.System.tester_type
                in (
                    "ATE4",
                    "ATE5",
                )
                else -85
            ),
            doc="Strong signal",
        ),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test Bluetooth signal strength."""
        dev["BLE"].uut = self.uuts[0]
        mes["rssi"]()


class Devices(share.Devices):
    """Devices. Uses SmartLink201 fixture."""

    vin_set = 12.0  # Injected Vin (V)

    def open(self):
        """Create all Instruments."""
        self["dcs_Vbatt"] = tester.DCSource(self.physical_devices["DCS1"])
        self["dcs_Vbatt"].output(self.vin_set, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_Vbatt"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (("rssi", "ScanRSSI", "RSSI", "Bluetooth signal strength"),)
        )
