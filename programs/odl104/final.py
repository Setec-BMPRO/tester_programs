#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Final Test Program."""

import tester
import share

from . import config


class Final(share.TestSequence):
    """ODL104 Final Test Program."""

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
        # Lookup the MAC address from the server
        mac = dev["serialtomac"].blemac_get(self.uuts[0].sernum)
        mes["ble_mac"].sensor.store(mac)
        mes["ble_mac"]()
        # Scan for the bluetooth transmission
        # Reply is like this: {
        #   'ad_data': {255: '1f050112022d624c3a00000300d1139e69'},
        #   'rssi': rssi,
        #   }
        reply = dev["pi_bt"].scan_advert_blemac(mac, timeout=20)
        mes["scan_mac"].sensor.store(reply is not None)
        mes["scan_mac"]()
        rssi = reply["rssi"]  # Received Signal Strength Indication
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
        # Connection to Serial To MAC server
        self["serialtomac"] = share.bluetooth.SerialToMAC()
        # Power to the units
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
        self["mirscan"] = sensor.Mirror()
        self["mirmac"] = sensor.Mirror()
        self["mirrssi"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ble_mac", "BleMac", "mirmac", "Get MAC address from server"),
                (
                    "scan_mac",
                    "ScanMac",
                    "mirscan",
                    "Scan for MAC address over Bluetooth",
                ),
                ("scan_rssi", "ScanRSSI", "mirrssi", "Bluetooth signal strength"),
            )
        )
