#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""TRS-BTx Initial Program."""

import pathlib
import time

import libtester
import serial
import tester

import share

from . import config
from . import console


class Initial(share.TestSequence):
    """TRS-BTS Initial Test Program."""

    vbatt = 12.0  # Injected Vbatt
    _limits = (
        libtester.LimitDelta("Vbat", vbatt, 0.5, doc="Battery input present"),
        libtester.LimitPercent("3V3", 3.3, 1.7, doc="3V3 present"),
        libtester.LimitLow("BrakeOff", 0.5, doc="Brakes off"),
        libtester.LimitDelta("BrakeOn", vbatt, 0.5, doc="Brakes on"),
        libtester.LimitLow("LightOff", 0.5, doc="Lights off"),
        libtester.LimitDelta("LightOn", vbatt, 0.25, doc="Lights on"),
        libtester.LimitLow("RemoteOff", 0.5, doc="Remote off"),
        libtester.LimitDelta("RemoteOn", vbatt, 0.25, doc="Remote on"),
        libtester.LimitLow("RedLedOff", 1.0, doc="Led off"),
        libtester.LimitDelta("RedLedOn", 1.8, 0.14, doc="Led on"),
        libtester.LimitLow("GreenLedOff", 1.0, doc="Led off"),
        libtester.LimitDelta("GreenLedOn", 2.5, 0.4, doc="Led on"),
        libtester.LimitLow("BlueLedOff", 1.0, doc="Led off"),
        libtester.LimitDelta("BlueLedOn", 2.65, 0.2, doc="Led on"),
        libtester.LimitDelta("Chem wire", 3.0, 0.5, doc="Voltage present"),
        libtester.LimitDelta("Sway- wire", 2.0, 0.5, doc="Voltage present"),
        libtester.LimitDelta("Sway+ wire", 1.0, 0.5, doc="Voltage present"),
        libtester.LimitPercent(
            "ARM-Vbatt", vbatt, 4.8, delta=0.088, doc="Voltage present"
        ),
        libtester.LimitPercent(
            "ARM-Vbatt-Cal", vbatt, 1.8, delta=0.088, doc="Voltage present"
        ),
        libtester.LimitDelta("ARM-Vpin", 0.0, 1.0, doc="Micro switch voltage ok"),
        libtester.LimitRegExp("BleMac", share.MAC.regex, doc="Valid MAC address"),
        libtester.LimitHigh("ScanRSSI", -100, doc="BLE signal"),
    )

    def open(self):
        """Prepare for testing."""
        self.config = config.get(self.parameter)
        Sensors.sw_image = self.config.sw_image
        self.configure(self._limits, Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("PgmNordic", self._step_program),
            tester.TestStep("Operation", self._step_operation),
            tester.TestStep("Calibrate", self._step_calibrate),
            tester.TestStep("Bluetooth", self._step_bluetooth),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        dev["dcs_vbat"].output(self.vbatt, True)
        self.measure(("dmm_vbat", "dmm_3v3", "dmm_chem"), timeout=5)
        if self.parameter == "BTS":
            self.measure(("dmm_sway-", "dmm_sway+"), timeout=5)
        mes["dmm_brakeoff"](timeout=5)
        dev["rla_pin"].remove()  # Relay contacts shorted
        self.measure(("dmm_brakeon", "dmm_lighton"), timeout=5)
        dev["rla_pin"].insert()

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        mes["JLink"]()

    @share.teststep
    def _step_operation(self, dev, mes):
        """Test the operation of LEDs."""
        trsbts = dev["trsbts"]
        trsbts.open()
        # Using device RESET results in sporadic duplicate startup banners
        # So, it's faster to just power cycle, than untangle the crappy console...
        dev["dcs_vbat"].output(0.0, delay=0.5)
        trsbts.reset_input_buffer()
        dev["dcs_vbat"].output(self.vbatt)
        trsbts.initialise(self.config.hw_version, self.uuts[0].sernum)
        self.measure(("dmm_redoff", "dmm_greenoff", "dmm_lightoff"), timeout=5)
        trsbts.override(share.console.parameter.OverrideTo.FORCE_ON)
        self.measure(
            ("dmm_remoteon", "dmm_redon", "dmm_greenon", "dmm_blueon"), timeout=5
        )
        trsbts.override(share.console.parameter.OverrideTo.FORCE_OFF)
        self.measure(
            ("dmm_remoteoff", "dmm_redoff", "dmm_greenoff", "dmm_blueoff"), timeout=5
        )
        trsbts.override(share.console.parameter.OverrideTo.NORMAL)

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate VBATT input voltage.

        Input voltage is at 12V, pin is IN, console is open.

        """
        trsbts = dev["trsbts"]
        mes["arm_vbatt"](timeout=5)
        # Battery calibration at nominal voltage
        dmm_v = mes["dmm_vbat"].stable(delta=0.002).value1
        trsbts["VBATT_CAL"] = dmm_v
        # Save new calibration settings
        trsbts["NVWRITE"] = True
        time.sleep(1)  # We seem to get a startup banner here sometimes
        mes["arm_vbatt_cal"](timeout=5)
        dev["rla_pin"].remove()
        mes["arm_vpin"](timeout=5)
        dev["rla_pin"].insert()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        mac = mes["ble_mac"]().value1
        # Save SerialNumber & MAC on a remote server.
        dev["BLE"].uut = self.uuts[0]
        dev["BLE"].mac = mac
        mes["rssi"]()


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("rla_pin", tester.Relay, "RLA3"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        pin = self["rla_pin"]
        pin.insert = pin.set_off  # N/O contacts
        pin.remove = pin.set_on
        # Serial connection to the console
        trsbts_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_port = self.port("NORDIC")
        trsbts_ser.port = nordic_port
        # trsbts Console driver
        self["trsbts"] = console.Console(trsbts_ser)

    def reset(self):
        """Reset instruments."""
        self["trsbts"].close()
        self["dcs_vbat"].output(0.0, False)
        self["rla_pin"].insert()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vbat"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vbat"].doc = "Across X1 and X2"
        self["3v3"] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self["3v3"].doc = "TP1"
        self["red"] = sensor.Vdc(dmm, high=2, low=2, rng=10, res=0.01)
        self["red"].doc = "Across red led"
        self["green"] = sensor.Vdc(dmm, high=2, low=3, rng=10, res=0.01)
        self["green"].doc = "Across green led"
        self["blue"] = sensor.Vdc(dmm, high=2, low=4, rng=10, res=0.01)
        self["blue"].doc = "Across blue led"
        self["chem"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self["chem"].doc = "TP11"
        self["sway-"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self["sway-"].doc = "TP12"
        self["sway+"] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self["sway+"].doc = "TP13"
        self["brake"] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.01)
        self["brake"].doc = "Brakes output"
        self["light"] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.01)
        self["light"].doc = "Lights output"
        self["remote"] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self["remote"].doc = "Remote output"
        # Console sensors
        trsbts = self.devices["trsbts"]
        for name, cmdkey, units in (
            ("arm_vbatt", "VBATT", "V"),
            ("arm_vpin", "VPIN", "V"),
        ):
            self[name] = sensor.Keyed(trsbts, cmdkey)
            self[name].units = units
        self["BleMac"] = sensor.Keyed(trsbts, "BT_MAC")
        self["BleMac"].on_read = lambda value: value.replace(":", "").lower()
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_image,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vbat", "Vbat", "vbat", "Battery input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("dmm_brakeoff", "BrakeOff", "brake", "Brakes output off"),
                ("dmm_brakeon", "BrakeOn", "brake", "Brakes output on"),
                ("dmm_lightoff", "LightOff", "light", "Lights output off"),
                ("dmm_lighton", "LightOn", "light", "Lights output on"),
                ("dmm_remoteoff", "RemoteOff", "remote", "Remote output off"),
                ("dmm_remoteon", "RemoteOn", "remote", "Remote output on"),
                ("dmm_redoff", "RedLedOff", "red", "Red led off"),
                ("dmm_redon", "RedLedOn", "red", "Red led on"),
                ("dmm_greenoff", "GreenLedOff", "green", "Green led off"),
                ("dmm_greenon", "GreenLedOn", "green", "Green led on"),
                ("dmm_blueoff", "BlueLedOff", "blue", "Blue led off"),
                ("dmm_blueon", "BlueLedOn", "blue", "Blue led on"),
                (
                    "dmm_chem",
                    "Chem wire",
                    "chem",
                    "Check for correct mounting of Chem Select wire",
                ),
                (
                    "dmm_sway-",
                    "Sway- wire",
                    "sway-",
                    "Check for correct mounting of Sway- wire",
                ),
                (
                    "dmm_sway+",
                    "Sway+ wire",
                    "sway+",
                    "Check for correct mounting of Sway+ wire",
                ),
                ("ble_mac", "BleMac", "BleMac", "Validate MAC address from console"),
                ("arm_vbatt", "ARM-Vbatt", "arm_vbatt", "Vbatt before cal"),
                ("arm_vbatt_cal", "ARM-Vbatt-Cal", "arm_vbatt", "Vbatt after cal"),
                ("arm_vpin", "ARM-Vpin", "arm_vpin", "Voltage on the pin microswitch"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
                ("rssi", "ScanRSSI", "RSSI", "Bluetooth signal strength"),
            )
        )
