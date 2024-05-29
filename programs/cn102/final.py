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
        super().open(limits, Devices, Sensors, Measurements)
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)
        self.sernum = None

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_sernum")
        reply = dev["pi_bt"].scan_advert_sernum(self.sernum, timeout=20)
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
        self["sernum"] = sensor.DataEntry(
            message=tester.translate("cn102_final", "msgSnEntry"),
            caption=tester.translate("cn102_final", "capSnEntry"),
        )
        self["sernum"].doc = "Barcode scanner"
        self["mirrssi"] = sensor.Mirror()


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ui_sernum", "SerNum", "sernum", "Unit serial number"),
                ("scan_rssi", "ScanRSSI", "mirrssi", "Bluetooth signal strength"),
            )
        )
