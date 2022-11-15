#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay Initial Test Program.

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

    # Input voltage to power the unit
    vin_set = 8.1
    # Common limits
    _common = (
        tester.LimitBetween(
            "Vin", vin_set - 1.1, vin_set - 0.1, doc="Input voltage present"
        ),
        tester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        tester.LimitLow("BkLghtOff", 0.5, doc="Backlight off"),
        tester.LimitBetween("BkLghtOn", 2.5, 3.5, doc="Backlight on"),
        # CAN Bus is operational if status bit 28 is set
        tester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN bus bound"),
    )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        "JD": {  # LPC1519 micro
            "Config": config.JDisplay,
            "Limits": _common
            + (
                tester.LimitRegExp(
                    "SwVer",
                    "^{0}$".format(config.JDisplay.sw_version.replace(".", r"\.")),
                ),
            ),
        },
        "RV": {  # LPC1519 micro
            "Config": config.RvView,
            "Limits": _common
            + (
                tester.LimitRegExp(
                    "SwVer",
                    "^{0}$".format(config.RvView.sw_version.replace(".", r"\.")),
                ),
            ),
        },
        "RV2": {  # LPC1519 micro
            "Config": config.RvView2,
            "Limits": _common
            + (
                tester.LimitRegExp(
                    "SwVer",
                    "^{0}$".format(config.RvView2.sw_version.replace(".", r"\.")),
                ),
            ),
        },
        "RV2A": {  # ATSAMC21 micro
            "Config": config.RvView2a,
            "Limits": _common + (tester.LimitRegExp("SwVer", "Dummy"),),
        },
    }

    def open(self, uut):
        """Prepare for testing."""
        self.config = self.config_data[self.parameter]["Config"]
        Devices.sw_file = Sensors.sw_file = self.config.sw_file
        super().open(
            self.config_data[self.parameter]["Limits"], Devices, Sensors, Measurements
        )
        self.is_atsam = self.parameter == "RV2A"
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
        arm.brand(self.config.hw_version, self.sernum, dev["rla_reset"])
        mes["sw_ver"]()

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
        armtunnel = dev["armtunnel"]
        armtunnel.open()
        mes["tunnel_swver"]()
        armtunnel.close()

    def _testmode(self, state):
        """Control of product testmode.

        @param state True for testmode ON

        """
        if self.is_atsam:
            header = tester.devphysical.can.SETECHeader()
            msg = header.message
            msg.device_id = share.can.SETECDeviceID.RVVIEW.value
            msg.msg_type = tester.devphysical.can.SETECMessageType.COMMAND.value
            msg.data_id = tester.devphysical.can.SETECDataID.XREG.value
            data = b"\xC5"  # XReg 0xC5 toggles testmode
            candev = self.physical_devices["_CAN"]
            candev.send(tester.devphysical.can.CANPacket(header, data))
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
        # Direct Console driver
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        # Console driver
        self["arm"] = console.DirectConsole(arm_ser)
        self["can"] = self.physical_devices["_CAN"]
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices["CAN"], share.can.SETECDeviceID.RVVIEW.value
        )
        self["armtunnel"] = console.TunnelConsole(tunnel)
        self["dcs_rst"].output(8.0, True)  # Fixture RESET circuit
        self.add_closer(lambda: self["dcs_rst"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["arm"].close()
        self["armtunnel"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_wd"):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    projectfile = "rvview2_atmel.jflash"
    sw_file = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        arm = self.devices["arm"]
        armtunnel = self.devices["armtunnel"]
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
            pathlib.Path(__file__).parent / self.projectfile,
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
        # Console sensors
        self["canbind"] = sensor.Keyed(arm, "CAN_BIND")
        self["swver"] = sensor.Keyed(arm, "SW_VER")
        self["tunnelswver"] = sensor.Keyed(armtunnel, "SW_VER")


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
                ("sw_ver", "SwVer", "swver", "Unit software version"),
                ("ui_yesnoon", "Notify", "oYesNoOn", "Button on"),
                ("ui_yesnooff", "Notify", "oYesNoOff", "Button off"),
                ("can_bind", "CAN_BIND", "canbind", "CAN bound"),
                ("tunnel_swver", "SwVer", "tunnelswver", "Unit software version"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
