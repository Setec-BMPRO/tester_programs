#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BLE2CAN Initial Program."""

import serial

import libtester
import share
import tester

from . import console


class Initial(share.TestSequence):
    """BLE2CAN Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Software binary version
    sw_version = "1.2.16964.2723"
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_version = (5, 0, "A")
    # Test limits
    limitdata = (
        libtester.LimitDelta("Vin", 12.0, 0.5, doc="Input voltage present"),
        libtester.LimitPercent("3V3", 3.3, 1.0, doc="3V3 present"),
        libtester.LimitPercent("5V", 5.0, 1.0, doc="5V present"),
        libtester.LimitHigh("RedLedOff", 3.1, doc="Led off"),
        libtester.LimitDelta("RedLedOn", 0.45, 0.05, doc="Led on"),
        libtester.LimitHigh("BlueLedOff", 3.1, doc="Led off"),
        libtester.LimitDelta("BlueLedOn", 0.3, 0.09, doc="Led on"),
        libtester.LimitHigh("GreenLedOff", 3.1, doc="Led off"),
        libtester.LimitLow("GreenLedOn", 0.2, doc="Led on"),
        libtester.LimitLow("TestPinCover", 0.5, doc="Cover in place"),
        libtester.LimitRegExp(
            "SwVer",
            "^{0}$".format(sw_version.replace(".", r"\.")),
            doc="Software version",
        ),
        libtester.LimitRegExp(
            "BtMac", "(?:[0-9A-F]{2}:?){5}[0-9A-F]{2}", doc="Valid MAC address"
        ),
        libtester.LimitHigh("ScanRSSI", -90, doc="BLE signal"),
        libtester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN bus bound"),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("TestArm", self._step_test_arm),
            tester.TestStep("Bluetooth", self._step_bluetooth),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        mes["dmm_tstpincov"](timeout=5)
        dev["ble2can"].open()
        dev["dcs_vin"].output(self.vbatt, True)
        self.measure(("dmm_vin", "dmm_3v3", "dmm_5v"), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test operation."""
        ble2can = dev["ble2can"]
        ble2can.brand(self.hw_version, self.uuts[0].sernum)
        self.measure(("SwVer", "dmm_redoff", "dmm_blueoff", "dmm_greenoff"), timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.FORCE_ON)
        self.measure(("dmm_redon", "dmm_blueon", "dmm_greenon"), timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.FORCE_OFF)
        self.measure(("dmm_redoff", "dmm_blueoff", "dmm_greenoff"), timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.NORMAL)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        btmac = share.MAC.loads(mes["BtMac"]().value1)
        dev["BLE"].uut = self.uuts[0]
        dev["BLE"].mac = btmac.dumps(separator="")
        dev["rla_pair_btn"].press()
        self._reset_unit()
        mes["rssi"]()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        dev["rla_pair_btn"].release()
        self._reset_unit()
        mes["CANbind"](timeout=10)

    def _reset_unit(self):
        """Reset the unit."""
        dev = self.devices
        dev["rla_reset"].pulse(0.1)
        dev["ble2can"].banner()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vfix", tester.DCSource, "DCS1"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("dcs_cover", tester.DCSource, "DCS5"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_pair_btn", tester.Relay, "RLA8"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use the relays
        pair = self["rla_pair_btn"]
        pair.press = pair.set_on
        pair.release = pair.set_off
        # Serial connection to the console
        ble2can_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        ble2can_ser.port = self.port("ARM")
        # Console driver
        self["ble2can"] = console.Console(ble2can_ser)
        # Apply power to fixture circuits.
        self["dcs_vfix"].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self["dcs_vfix"].output(0.0, output=False))
        self["dcs_cover"].output(9.0, output=True)
        self.add_closer(lambda: self["dcs_cover"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["ble2can"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_reset", "rla_pair_btn"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "X1/X2"
        self["3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3v3"].doc = "U4 output"
        self["5v"] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.01)
        self["5v"].doc = "U5 output"
        self["red"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self["red"].doc = "Led cathode"
        self["green"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self["green"].doc = "Led cathode"
        self["blue"] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self["blue"].doc = "Led cathode"
        self["tstpin_cover"] = sensor.Vdc(dmm, high=16, low=1, rng=100, res=0.01)
        self["tstpin_cover"].doc = "Photo sensor"
        # Console sensors
        ble2can = self.devices["ble2can"]
        self["CANbind"] = sensor.Keyed(ble2can, "CAN_BIND")
        for name, cmdkey in (
            ("BtMac", "BT_MAC"),
            ("SwVer", "SW_VER"),
        ):
            self[name] = sensor.Keyed(ble2can, cmdkey)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("dmm_5v", "5V", "5v", "5V rail voltage"),
                ("dmm_redoff", "RedLedOff", "red", "Red led off"),
                ("dmm_redon", "RedLedOn", "red", "Red led on"),
                ("dmm_greenoff", "GreenLedOff", "green", "Green led off"),
                ("dmm_greenon", "GreenLedOn", "green", "Green led on"),
                ("dmm_blueoff", "BlueLedOff", "blue", "Blue led off"),
                ("dmm_blueon", "BlueLedOn", "blue", "Blue led on"),
                (
                    "dmm_tstpincov",
                    "TestPinCover",
                    "tstpin_cover",
                    "Cover over BC2 test pins",
                ),
                ("BtMac", "BtMac", "BtMac", "MAC address"),
                ("rssi", "ScanRSSI", "RSSI", "Bluetooth RSSI Level"),
                ("SwVer", "SwVer", "SwVer", "Unit software version"),
                ("CANbind", "CAN_BIND", "CANbind", "CAN bound"),
            )
        )
