#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd
"""BC60 Initial Test Program."""

import pathlib

import libtester
import serial
import tester

import share
from . import console


class Initial(share.TestSequence):
    """Initial Test Program."""

    initial_limits = (
        libtester.LimitLow("LockClosed", 200, doc="Fixture switch closed"),
        libtester.LimitDelta("240Vac", 240.0, 5.0, doc="AC ok"),
        libtester.LimitPercent("340V", 340.0, 5.0, doc="340V ok"),
        libtester.LimitBetween("400V", 405.0, 434.0, doc="400V ok"),
        libtester.LimitBetween("12VPri", 13.0, 14.0, doc="12Vpri ok"),
        libtester.LimitBetween("12VPri_Relay", 11.25, 12.5, doc="12VPri_Relay ok"),
        libtester.LimitBetween("15Vsb", 12.0, 13.0, doc="15Vsb ok"),
        libtester.LimitBetween("3V3", 3.275, 3.330, doc="3V3 ok"),
        libtester.LimitBetween("5V", 4.68, 5.13, doc="5V ok"),
        libtester.LimitBetween("CAN_PWR", 11.8, 13.0, doc="CAN_PWR ok"),
        libtester.LimitPercent("Vout", 13.0, 5.0),
    )

    def open(self):
        """Prepare for testing."""
        Sensors.ble_image = "bl652_hci_uart_v1.0.0-0-ga43a850.hex"
        Sensors.stm_image = "bc60_v1.0.2-0-g65bd136-signed-mcuboot-factory.hex"
        self.configure(self.initial_limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Load", self._step_load),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare: Dc input, measure."""
        dev["dcs_sec"].output(13.0, output=True)
        self.measure(
            (
                "FixtureShut",
                "15Vsb",
                "5V",
                "3V3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program both devices."""
        with dev["swd_select"]:
            mes["JLinkBLE"]()
        mes["JLinkSTM"]()
        dev["dcs_sec"].output(0.0, output=False)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up the unit."""
        dev["acsource"].output(voltage=240.0, output=True, delay=1.0)
        dev["dcl_Vout"].output(0.1, output=True)
        self.measure(
            (
                "240Vac",
                "340V",
                "12VPri",
                "12VPri_Relay",
                "15Vsb",
                "5V",
                "3V3",
            ),
            timeout=5,
        )
        con = dev["con"]
        con.open()
        con.brand(self.uuts[0].sernum, "05A", "05A")
        con.startup(13.5, 60.0)
        self.measure(
            (
                "400V",
                "Vout",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_load(self, dev, mes):
        """Test load."""
        dcl = dev["dcl_Vout"]
        for load in range(0, 61, 10):
            with tester.PathName("{0}A".format(load)):
                dcl.output(load, delay=0.5)
                mes["Vout"](timeout=5)
        dcl.output(1.0)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_sec", tester.DCSource, "DCS1"),
            ("swd_select", tester.Relay, "RLA1"),  # Off: STM, On: Laird BLE
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcl_Vout"] = tester.DCLoadParallel(
            (
                (tester.DCLoad(self.physical_devices["DCL1"]), 10),
                (tester.DCLoad(self.physical_devices["DCL3"]), 10),
            )
        )
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = self.port("STM")
        self["con"] = console.Console(con_ser)

    def reset(self):
        """Reset instruments."""
        self["con"].close()
        self["acsource"].reset()
        self["dcl_Vout"].output(10.0, delay=1.0)
        self["discharge"].pulse()
        self["dcl_Vout"].output(0.0, output=False)
        self["dcs_sec"].output(0.0, output=False)
        self["swd_select"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    ble_image = None
    stm_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["lock"] = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self["lock"].doc = "Fixture microswitch"
        self["Vac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self["Vac"].doc = "240Vac input"
        self["400V"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self["400V"].doc = "400V bus"
        self["12VPri"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self["12VPri"].doc = "12VPri bus"
        self["12VPri_Relay"] = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self["12VPri_Relay"].doc = "Power to K1"
        self["15Vsb"] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self["15Vsb"].doc = "15Vsb rail"
        self["5V"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["5V"].doc = "5V rail"
        self["3V3"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.001)
        self["3V3"].doc = "3V3 rail"
        self["Vout"] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self["Vout"].doc = "Output"
        self["ACfan"] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.01)
        self["ACfan"].doc = "AC fan X201"
        self["DCfan"] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self["DCfan"].doc = "DC fan X202"
        self["Vcan"] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.01)
        self["Vcan"].doc = "CAN power"
        # Progamming
        self["JLinkBLE"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.ble_image,
        )
        self["JLinkBLE"].doc = "BLE programmer"
        self["JLinkSTM"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile("stm32l496vg"),
            pathlib.Path(__file__).parent / self.stm_image,
        )
        self["JLinkSTM"].doc = "STM programmer"
        # Console
        con = self.devices["con"]
        self["msp_stat"] = sensor.Keyed(con, "MSP-STATUS")
        self["msp_stat"].doc = "MSP430 console"
        self["msp_vo"] = sensor.Keyed(con, "MSP-VOUT")
        self["msp_vo"].doc = "MSP430 console"


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("FixtureShut", "LockClosed", "lock", "Fixture lid closed"),
                ("JLinkBLE", "ProgramOk", "JLinkBLE", "BLE Programmed"),
                ("JLinkSTM", "ProgramOk", "JLinkSTM", "STM Programmed"),
                ("240Vac", "240Vac", "Vac", "AC fuse fitted"),
                ("340V", "340V", "400V", "PFC not running"),
                ("400V", "400V", "400V", "PFC running"),
                ("12VPri", "12VPri", "12VPri", "12VPri running"),
                ("12VPri_Relay", "12VPri_Relay", "12VPri_Relay", "12VPri_Relay running"),
                ("15Vsb", "15Vsb", "15Vsb", "15Vsb running"),
                ("5V", "5V", "5V", "5V running"),
                ("3V3", "3V3", "3V3", "3V3 running"),
                ("Vout", "Vout", "Vout", "Output"),
            )
        )
