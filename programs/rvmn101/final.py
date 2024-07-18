#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Final Test Program."""

import libtester
import tester

import share
from . import config


class Final(share.TestSequence):
    """RVMN101 and RVMN5x Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        rssi = -70 if self.tester_type in ("ATE4", "ATE5") else -85
        if self.parameter == "101B":  # 101B 3dB below the other versions
            rssi -= 3
        limits = self.cfg.limits_final() + (
            libtester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
        )
        self.configure(limits, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev["dcs_vin"].output(self.cfg.vbatt_set, True, delay=2.0)
        dev["BLE"].uut = self.uuts[0]
        mac = dev["BLE"].mac
        mes["BLE_MAC"].sensor.store(mac)
        mes["BLE_MAC"]()
        mes["RSSI"]()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        self["dcs_vin"] = tester.DCSource(self.physical_devices["DCS1"])

    def reset(self):
        """Reset instruments."""
        self["dcs_vin"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self["ble_mac"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("BLE_MAC", "BleMac", "ble_mac", "Get MAC address from server"),
                ("RSSI", "ScanRSSI", "RSSI", "Bluetooth signal strength"),
            )
        )
