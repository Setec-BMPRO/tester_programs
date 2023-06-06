#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay Initial Test Program.

Shares the test fixture with the RVMD50 program.

The ATSAMC21 version does not do:
- Serial console.
- Console tunnel over CAN.
It's testmode is controlled using CAN packets.

"""

import pathlib

import attr
import serial
import tester

import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RvView/JDisplay Initial Test Program."""

    vin_set = 8.1  # Input voltage to power the unit
    _limits = (
        tester.LimitBetween(
            "Vin", vin_set - 1.1, vin_set - 0.1, doc="Input voltage present"
        ),
        tester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        tester.LimitLow("BkLghtOff", 0.5, doc="Backlight off"),
        tester.LimitBetween("BkLghtOn", 2.5, 3.5, doc="Backlight on"),
        # CAN Bus is operational if status bit 28 is set
        tester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN bus bound"),
    )

    def open(self, uut):
        """Prepare for testing."""
        self.config = config.get(self.parameter)
        self.is_atsam = self.config.is_atsam
        Devices.sw_file = Sensors.sw_file = self.config.sw_file
        super().open(self._limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise, not self.is_atsam),
            tester.TestStep("Display", self._step_display),
            tester.TestStep("CanBus", self._step_canbus, not self.is_atsam),
        )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_sernum")
        dev["dcs_vin"].output(self.vin_set, True)
        self.measure(("dmm_vin", "dmm_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        if self.is_atsam:
            mes["JLink"]()  # A measurement
        else:
            dev["programmer"].program()  # A device

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the LPC1519 micro.

        Set HW version & Serial number.

        """
        arm = dev["arm"]
        arm.open()
        dev["rla_reset"].pulse(0.1)
        arm.brand(self.config.hw_version, self.sernum)

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD and button.

        Put device into test mode.
        Check all segments and backlight.

        """
        dev["rla_reset"].pulse(0.1, delay=4)
        self._testmode(True)
        self.measure(
            ("ui_yesnoon", "dmm_bklghton", "ui_yesnooff", "dmm_bklghtoff"), timeout=5
        )
        self._testmode(False)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        mes["can_bind"](timeout=10)

    def _testmode(self, state):
        """Control of product testmode.

        @param state True for testmode ON

        """
        if self.is_atsam:
            testmode = share.can.RvviewTestModeBuilder()
            candev = self.physical_devices["_CAN"]
            candev.send(testmode.packet)
        else:
            self.devices["arm"].testmode(state)


@attr.s
class LatchingRelay:

    """A latching relay, with 'on' and 'off' drive lines."""

    rla_on = attr.ib()
    rla_off = attr.ib()
    _pulse_time = attr.ib(init=False, default=0.01)

    def set_on(self):
        """Set ON."""
        self.rla_on.pulse(self._pulse_time)

    def set_off(self):
        """Set OFF."""
        self.rla_off.pulse(self._pulse_time)

    def pulse(self, duration=2.0, delay=0):
        """Pulse output ON for a time."""
        self.rla_on.pulse(self._pulse_time, delay=duration)
        self.rla_off.pulse(self._pulse_time, delay=delay)


class Devices(share.Devices):

    """Devices."""

    sw_file = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_rst", tester.DCSource, "DCS1"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("rla_rst_on", tester.Relay, "RLA1"),
            ("rla_rst_off", tester.Relay, "RLA2"),
            ("rla_boot", tester.Relay, "RLA3"),
            ("rla_wd", tester.Relay, "RLA4"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["rla_reset"] = LatchingRelay(self["rla_rst_on"], self["rla_rst_off"])
        arm_port = share.config.Fixture.port("029687", "ARM")
        # LPC1519 device programmer
        self["programmer"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_file,
            crpmode=False,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        self["arm"] = console.Console(arm_ser)
        self["dcs_rst"].output(8.0, True)  # Fixture RESET circuit
        self.add_closer(lambda: self["dcs_rst"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["arm"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_wd"):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    sw_file = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["mir_can"] = sensor.Mirror()
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "X1"
        self["3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3v3"].doc = "U1 output"
        self["bklght"] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self["bklght"].doc = "Across backlight"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("atsamc21e17"),
            pathlib.Path(__file__).parent / self.sw_file,
        )
        self["sernum"] = sensor.DataEntry(
            message=tester.translate("rvview_jdisplay_initial", "msgSnEntry"),
            caption=tester.translate("rvview_jdisplay_initial", "capSnEntry"),
            timeout=300,
        )
        self["sernum"].doc = "Barcode scanner"
        self["oYesNoOn"] = sensor.YesNo(
            message=tester.translate("rvview_jdisplay_initial", "PushButtonOn?"),
            caption=tester.translate("rvview_jdisplay_initial", "capButtonOn"),
        )
        self["oYesNoOn"].doc = "Operator input"
        self["oYesNoOff"] = sensor.YesNo(
            message=tester.translate("rvview_jdisplay_initial", "PushButtonOff?"),
            caption=tester.translate("rvview_jdisplay_initial", "capButtonOff"),
        )
        self["oYesNoOff"].doc = "Operator input"
        self["canbind"] = sensor.Keyed(self.devices["arm"], "CAN_BIND")


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3", "3V3", "3v3", "3V3 rail voltage"),
                ("dmm_bklghtoff", "BkLghtOff", "bklght", "Test backlight"),
                ("dmm_bklghton", "BkLghtOn", "bklght", "Test backlight"),
                ("ui_sernum", "SerNum", "sernum", "Unit serial number"),
                ("ui_yesnoon", "Notify", "oYesNoOn", "Button on"),
                ("ui_yesnooff", "Notify", "oYesNoOff", "Button off"),
                ("can_bind", "CAN_BIND", "canbind", "CAN bound"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
