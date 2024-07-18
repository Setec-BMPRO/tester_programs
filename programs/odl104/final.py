#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Final Test Program."""

import tester
import share

from . import config


class Final(share.TestSequence):
    """ODL104 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        limits = self.cfg.limits_final
        self.configure(limits, Devices, Sensors, Measurements)
        rssi_lim = -70 if self.tester_type in ("ATE4", "ATE5") else -85
        self.limits["ScanRSSI"].adjust(rssi_lim)
        self.ble_rssi_dev()
        super().open()
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev["BLE"].uut = self.uuts[0]
        mac = dev["BLE"].mac
        mes["ble_mac"].sensor.store(mac)
        mes["ble_mac"]()
        mes["rssi"]()


class Devices(share.Devices):
    """Devices. Uses Trek/JControl fixture."""

    vbatt = 12.0  # Injected Vbatt

    def open(self):
        """Create all Instruments."""
        self["dcs_vbat"] = tester.DCSource(self.physical_devices["DCS1"])
        self["dcs_vbat"].output(self.vbatt, output=True)
        self.add_closer(lambda: self["dcs_vbat"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self["mirmac"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ble_mac", "BleMac", "mirmac", "Get MAC address from server"),
                ("rssi", "ScanRSSI", "RSSI", "Bluetooth RSSI Level"),
            )
        )
