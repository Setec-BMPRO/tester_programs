#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import tester

import share


class Final(share.TestSequence):

    """SmartLink201 Final Test Program."""

    limitdata = (
        tester.LimitHigh(
            "ScanRSSI",
            -70
            if share.config.System.tester_type
            in (
                "ATE4",
                "ATE5",
            )
            else -85,
            doc="Strong signal",
        ),
    )
    sernum = None

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test Bluetooth signal strength."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_sernum")
        # Lookup the MAC address from the server
        mac = dev["serialtomac"].blemac_get(self.sernum)
        reply = dev["pi_bt"].scan_advert_blemac(mac, timeout=20)
        rssi = reply["rssi"] if reply else float("NaN")
        mes["scan_RSSI"].sensor.store(rssi)
        mes["scan_RSSI"]()


class Devices(share.Devices):

    """Devices. Uses SmartLink201 fixture."""

    vin_set = 12.0  # Injected Vin (V)

    def open(self):
        """Create all Instruments."""
        # Connection to Serial To MAC server
        self["serialtomac"] = share.bluetooth.SerialToMAC()
        # Connection to RaspberryPi bluetooth server
        self["pi_bt"] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url()
        )
        # Power to the unit
        self["dcs_Vbatt"] = tester.DCSource(self.physical_devices["DCS1"])
        self["dcs_Vbatt"].output(self.vin_set, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_Vbatt"].output(0.0, output=False))


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self["SnEntry"] = sensor.DataEntry(
            message=tester.translate("smartlink201_final", "msgSnEntry"),
            caption=tester.translate("smartlink201_final", "capSnEntry"),
        )
        self["SnEntry"].doc = "Entered S/N"
        self["mir_RSSI"] = sensor.Mirror()
        self["mir_RSSI"].doc = "Measured RSSI"


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ui_sernum", "SerNum", "SnEntry", "S/N valid"),
                ("scan_RSSI", "ScanRSSI", "mir_RSSI", "Bluetooth signal strength"),
            )
        )
