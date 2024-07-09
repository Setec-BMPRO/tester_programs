#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""TRS-BTx Final Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """TRS-BTS Final Test Program."""

    vbatt = 12.0  # Injected Vbatt
    rssi = -70 if share.config.System.tester_type in ("ATE4", "ATE5") else -85
    pc29164_lots = (  # PC-29164 for TRS-BT2 - Use BLE with chip antenna
        "A220815",
        "A220816",
        "A220913",
        "A221004",
        "A221017",
        "A221102",
        "A221112",
        "A221202",
        "A221217",
        "A221303",
        "A221316",
        "A221317",
        "A221411",
        "A221412",
        "A221614",
        "A221702",
        "A221703",
    )
    pc29164_rssi = -90 if share.config.System.tester_type in ("ATE4", "ATE5") else -100
    limitdata = (
        libtester.LimitDelta("Vbat", vbatt, 0.5, doc="Battery input present"),
        libtester.LimitLow("BrakeOff", 0.5, doc="Brakes off"),
        libtester.LimitDelta("BrakeOn", vbatt, 0.5, doc="Brakes on"),
        libtester.LimitRegExp("BleMac", share.MAC.regex, doc="Valid MAC address"),
        libtester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
        libtester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (
            tester.TestStep("Pin", self._step_pin),
            tester.TestStep("Bluetooth", self._step_bluetooth),
        )
        # PC-29164 for TRS-BT2 - Use BLE with chip antenna
        uut = self.uuts[0]
        if uut and uut.lot.number in self.pc29164_lots:
            self.limits["ScanRSSI"].adjust(self.pc29164_rssi)

    @share.teststep
    def _step_pin(self, dev, mes):
        """Test the Pull-Pin operation."""
        dev["dcs_vbat"].output(self.vbatt, True)
        self.measure(
            (
                "dmm_vbat",
                "dmm_brakeon",  # Pin OUT: Brakes ON
                "ui_pin",  # Operator puts the pin IN
                "dmm_brakeoff",  # Pin IN: Brakes OFF
            ),
            timeout=5,
        )

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        # Power cycle or BLE won't Tx after pin was out...
        dev["dcs_vbat"].output(0.0, delay=1.0)
        dev["dcs_vbat"].output(self.vbatt)
        # Lookup the MAC address from the server
        dev["BLE"].uut = self.uuts[0]
        mac = dev["BLE"].mac
        mes["ble_mac"].sensor.store(mac)
        self.measure(
            (
                "ble_mac",
                "rssi",
            )
        )


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["dcs_vbat"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vbat"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self["vbat"].doc = "DC input of fixture"
        self["pin_in"] = sensor.Notify(
            message=tester.translate("trsbtx_final", "msgPinIn"),
            caption=tester.translate("trsbtx_final", "capPinIn"),
        )
        self["brake"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self["brake"].doc = "Brake output"
        self["mirmac"] = sensor.Mirror()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vbat", "Vbat", "vbat", "Battery input voltage"),
                ("ui_pin", "Notify", "pin_in", "Operator inserts pin"),
                ("dmm_brakeoff", "BrakeOff", "brake", "Brakes output off"),
                ("dmm_brakeon", "BrakeOn", "brake", "Brakes output on"),
                ("ble_mac", "BleMac", "mirmac", "Get MAC address from server"),
                ("rssi", "ScanRSSI", "RSSI", "Bluetooth signal strength"),
            )
        )
