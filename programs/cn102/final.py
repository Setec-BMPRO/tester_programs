#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd
"""CN102/3 Final Test Program."""

import tester

import share
from . import config


class Final(share.TestSequence):
    """CN102/3 Final Test Program."""

    def open(self, uut):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, uut)
        limits = self.cfg.limits_final
        super().configure(limits, Devices, Sensors, Measurements)
        super().open(uut)
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        reply = dev["pi_bt"].scan_advert_sernum(self.uuts[0].sernum, timeout=20)
        if reply:
            rssi = reply["rssi"]
        else:
            rssi = float("NaN")
        mes["scan_rssi"].sensor.store(rssi)
        mes["scan_rssi"]()


class Devices(share.Devices):
    """Devices. Uses Trek/JControl fixture."""

    vbatt = 12.0  # Injected Vbatt

    def open(self):
        """Create all Instruments."""
        # Connection to RaspberryPi bluetooth server
        self["pi_bt"] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url()
        )
        # Power to the units
        self["dcs_vbat"] = tester.DCSource(self.physical_devices["DCS1"])
        self["dcs_vbat"].output(self.vbatt, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_vbat"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self["mirrssi"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (("scan_rssi", "ScanRSSI", "mirrssi", "Bluetooth signal strength"),)
        )
