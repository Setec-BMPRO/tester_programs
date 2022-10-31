#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Initial Test Program."""

import pathlib

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):

    """RVMN101 and RVMN5x Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        Devices.fixture = self.cfg.fixture
        Devices.arm_image = self.cfg.arm_image
        Devices.nordic_image = self.cfg.nordic_image
        Devices.reversed_output_dict = self.cfg.reversed_output_dict
        Sensors.nordic_projectfile = self.cfg.nordic_projectfile
        Sensors.nordic_image = self.cfg.nordic_image
        Sensors.arm_projectfile = self.cfg.arm_projectfile
        Sensors.arm_image = self.cfg.arm_image
        self.limits = self.cfg.limits_initial()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise),
            tester.TestStep("Output", self._step_output),
            tester.TestStep("CanBus", self._step_canbus),
        )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_serialnum")
        dev["dcs_vbatt"].output(self.cfg.vbatt_set, output=True)
        self.measure(
            (
                "dmm_vbatt",
                "dmm_3v3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program both devices."""
        mes["JLinkARM"]()
        with dev["swd_select"]:
            mes["JLinkBLE"]()

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the unit."""
        # Open console serial connection
        rvmn101 = dev["rvmn101"]
        rvmn101.open()
        # Cycle power to restart the unit
        dev["dcs_vbatt"].output(output=False, delay=1.5)
        dev["dcs_vbatt"].output(output=True, delay=2.0)
        rvmn101.brand(self.sernum, self.cfg.product_rev, self.cfg.hardware_rev)
        # Save SerialNumber & MAC on a remote server.
        mac = mes["ble_mac"]().reading1
        dev["serialtomac"].blemac_set(self.sernum, mac)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the outputs of the unit."""
        rvmn101 = dev["rvmn101"]
        if self.parameter == "101A":
            rvmn101.hs_output(41, False)  # Defaults to on, so we turn it off.
        # Reversed HBridge outputs are only on 101A Rev 7-9
        if rvmn101.reversed_outputs:
            # Turn LOW, then HIGH, reversed HBridge outputs in turn
            with dev["rla_pullup"]:
                for idx in rvmn101.reversed_outputs:
                    with tester.PathName("REV{0}".format(idx)):
                        rvmn101.hs_output(idx, True)
                        mes["dmm_hb_on"](timeout=1)
                        rvmn101.hs_output(idx, False)
                        mes["dmm_hb_off"](timeout=1)
        mes["dmm_hs_off"](timeout=1)
        # Measurements from here on do not fail the test instantly.
        # Always measure all the outputs, and force a fail if any output
        # has failed. So we get a full dataset on every test.
        with share.MultiMeasurementSummary(default_timeout=2) as checker:
            # Turn ON, then OFF, each HS output in turn
            for idx in rvmn101.normal_outputs:
                with tester.PathName(rvmn101.pin_name(idx)):
                    rvmn101.hs_output(idx, True)
                    checker.measure(mes["dmm_hs_on"])
                    rvmn101.hs_output(idx, False)
                    checker.measure(mes["dmm_hs_off"])
            # Turn ON, then OFF, each LS output in turn
            for idx, dmm_channel in (
                (rvmn101.ls_0a5_out1, "dmm_ls1"),
                (rvmn101.ls_0a5_out2, "dmm_ls2"),
            ):
                rvmn101.ls_output(idx, True)
                checker.measure(mes[dmm_channel + "_on"])
                rvmn101.ls_output(idx, False)
                checker.measure(mes[dmm_channel + "_off"])

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        with dev["canreader"]:
            mes["can_active"]()


class Devices(share.Devices):

    """Devices."""

    fixture = None  # Fixture number
    arm_image = None  # ARM software image filename
    nordic_image = None  # Nordic software image filename
    reversed_output_dict = None  # Outputs with reversed operation

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vbatt", tester.DCSource, "DCS1"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_pullup", tester.Relay, "RLA3"),
            ("swd_select", tester.Relay, "RLA4"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        nordic_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_ser.port = share.config.Fixture.port(self.fixture, "NORDIC")
        # Console driver
        console_class = {
            "101A": console.Console101A,
            "101B": console.Console101B,
            "50": console.Console50,
            "55": console.Console55,
        }[self.parameter]
        console_class.reversed_output_dict = self.reversed_output_dict
        self["rvmn101"] = console_class(nordic_ser)
        # CAN devices
        self["can"] = self.physical_devices["_CAN"]
        self["canreader"] = tester.CANReader(self["can"])
        self["candetector"] = share.can.PacketDetector(self["canreader"])
        # Connection to Serial To MAC server
        self["serialtomac"] = share.bluetooth.SerialToMAC()

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["rvmn101"].close()
        self["canreader"].stop()
        self["can"].rvc_mode = False
        self["dcs_vbatt"].output(0.0, False)
        for rla in (
            "rla_reset",
            "rla_pullup",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    nordic_projectfile = None
    nordic_image = None
    arm_projectfile = None
    arm_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["VBatt"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["3V3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["HSout"] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.1)
        self["ReverseHB"] = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.1)
        self["LSout1"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.1)
        self["LSout2"] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        self["SnEntry"] = sensor.DataEntry(
            message=tester.translate("rvmn101_initial", "msgSnEntry"),
            caption=tester.translate("rvmn101_initial", "capSnEntry"),
        )
        self["JLinkBLE"] = sensor.JLink(
            self.devices["JLink"],
            pathlib.Path(__file__).parent / self.nordic_projectfile,
            pathlib.Path(__file__).parent / self.nordic_image,
        )
        self["JLinkARM"] = sensor.JLink(
            self.devices["JLink"],
            pathlib.Path(__file__).parent / self.arm_projectfile,
            pathlib.Path(__file__).parent / self.arm_image,
        )
        # Console sensors
        rvmn101 = self.devices["rvmn101"]
        self["SwRev"] = sensor.KeyedReadingString(rvmn101, "SW-REV")
        self["SwRev"].doc = "Nordic software version"
        self["BleMac"] = sensor.KeyedReadingString(rvmn101, "MAC")
        self["BleMac"].doc = "Nordic BLE MAC"
        # Convert "xx:xx:xx:xx:xx:xx (random)" to "xxxxxxxxxxxx"
        self["BleMac"].on_read = lambda value: value.replace(":", "").replace(
            " (random)", ""
        )
        self["cantraffic"] = sensor.KeyedReadingBoolean(
            self.devices["candetector"], None
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_3v3", "3V3", "3V3", "Micro power ok"),
                ("dmm_vbatt", "Vbatt", "VBatt", "Battery input ok"),
                ("dmm_hs_on", "HSon", "HSout", "High-side driver ON"),
                ("dmm_hs_off", "HSoff", "HSout", "All high-side drivers OFF"),
                ("dmm_hb_on", "HBon", "ReverseHB", "Test reversed HBridge 1-3 ON"),
                ("dmm_hb_off", "HBoff", "ReverseHB", "Test reversed HBridge 1-3 OFF"),
                ("dmm_ls1_on", "LSon", "LSout1", "Low-side driver1 ON"),
                ("dmm_ls1_off", "LSoff", "LSout1", "Low-side driver1 OFF"),
                ("dmm_ls2_on", "LSon", "LSout2", "Low-side driver2 ON"),
                ("dmm_ls2_off", "LSoff", "LSout2", "Low-side driver2 OFF"),
                ("ui_serialnum", "SerNum", "SnEntry", ""),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
                ("ble_mac", "BleMac", "BleMac", "MAC address"),
                ("JLinkARM", "ProgramOk", "JLinkARM", "Programmed"),
                ("JLinkBLE", "ProgramOk", "JLinkBLE", "Programmed"),
            )
        )
