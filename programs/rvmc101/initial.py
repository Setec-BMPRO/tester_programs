#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101x Initial Test Program."""

import pathlib

import libtester
import tester

import share
from . import display


class Initial(share.TestSequence):
    """RVMC101x Initial Test Program."""

    sw_image = {
        "ATMEL": "rvmc101_sam_2.1.0-0-g3780794.bin",
        "LITE": "None",
        "NXP": "rvmc101_0.4.bin",
    }
    limitdata = (
        libtester.LimitDelta("Vin", 12.0, 0.5, doc="Input voltage present"),
        libtester.LimitPercent("3V3", 3.3, 3, doc="3V3 present"),
        libtester.LimitPercent("5V", 5.0, 5, doc="5V present"),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
    )
    is_full = None  # False if 'Lite' version (no micro fitted)

    def open(self):
        """Create the test program as a linear sequence."""
        Devices.sw_image = Sensors.sw_image = self.sw_image[self.parameter]
        self.is_full = self.parameter != "LITE"
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program, self.is_full),
            tester.TestStep("Display", self._step_display, self.is_full),
            tester.TestStep("CanBus", self._step_canbus, self.is_full),
        )

    def _positions(self):
        """Range of my active PCB positions.

        @return range instance of PCB position numbers (1-N)

        """
        return range(1, self.per_panel + 1)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["dcs_vin"].output(12.0, output=True, delay=1)
        mes["dmm_vin"](timeout=5)
        name = "dmm" if self.is_full else "dmm_lite"
        for pos in self._positions():
            self.measure(mes[name][pos], timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        sel = dev["selector"]
        for pos in self._positions():
            if tester.Measurement.position_enabled(pos):
                with sel[pos]:
                    if self.parameter == "NXP":
                        pgm = dev["program_arm"]
                        pgm.position = pos
                        pgm.program()  # A device
                    else:
                        pgm = mes["JLink"]
                        pgm.sensor.position = pos
                        pgm()  # A measurement

    @share.teststep
    def _step_display(self, dev, mes):
        """Check all 7-segment displays."""
        dev["rla_reset"].pulse(0.01)  # Opto, not a relay
        sel = dev["selector"]
        mes_dis = mes["ui_yesnodisplay"]
        for pos in self._positions():
            if tester.Measurement.position_enabled(pos):
                mes_dis.sensor.position = pos
                with sel[pos]:
                    with dev["display"]:
                        mes_dis()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        sel = dev["selector"]
        mes_can = mes["can_active"]
        can_rdr = dev["canreader"]
        for pos in self._positions():
            if tester.Measurement.position_enabled(pos):
                mes_can.sensor.position = pos
                with sel[pos]:
                    with can_rdr:
                        mes_can()


class Devices(share.Devices):
    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS1"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
            ("rla_pos1", tester.Relay, "RLA3"),
            ("rla_pos2", tester.Relay, "RLA4"),
            ("rla_pos3", tester.Relay, "RLA5"),
            ("rla_pos4", tester.Relay, "RLA6"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # CAN devices
        self["can"] = self.physical_devices["CAN"]
        self["canreader"] = tester.CANReader(self["can"])
        self["candetector"] = share.can.PacketDetector(self["canreader"])
        self["display"] = display.LEDControl(self["can"])
        arm_port = self.port("ARM")
        self["program_arm"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_image,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        self["selector"] = [  # This is indexed using position (1-N)
            None,
            self["rla_pos1"],
            self["rla_pos2"],
            self["rla_pos3"],
            self["rla_pos4"],
        ]

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["canreader"].stop()
        self["can"].rvc_mode = False
        self["dcs_vin"].output(0.0, False)
        for rla in (
            "rla_reset",
            "rla_boot",
            "rla_pos1",
            "rla_pos2",
            "rla_pos3",
            "rla_pos4",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(
            dmm, high=1, low=1, rng=100, res=0.01, position=(1, 2, 3, 4)
        )
        self["a_3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01, position=1)
        self["b_3v3"] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01, position=2)
        self["c_3v3"] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.01, position=3)
        self["d_3v3"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01, position=4)
        self["a_5v"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01, position=1)
        self["b_5v"] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01, position=2)
        self["c_5v"] = sensor.Vdc(dmm, high=8, low=1, rng=10, res=0.01, position=3)
        self["d_5v"] = sensor.Vdc(dmm, high=9, low=1, rng=10, res=0.01, position=4)
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile("atsamc21e16"),
            pathlib.Path(__file__).parent / self.sw_image,
        )
        self["yesnodisplay"] = sensor.YesNo(
            message=tester.translate("rvmc101_initial", "DisplaysOn?"),
            caption=tester.translate("rvmc101_initial", "capDisplay"),
            position=(1, 2, 3, 4),
        )
        self["yesnodisplay"].doc = "Tester operator"
        self["cantraffic"] = sensor.Keyed(self.devices["candetector"], None)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
                ("dmm_3v3a", "3V3", "a_3v3", "3V3 ok"),
                ("dmm_3v3b", "3V3", "b_3v3", "3V3 ok"),
                ("dmm_3v3c", "3V3", "c_3v3", "3V3 ok"),
                ("dmm_3v3d", "3V3", "d_3v3", "3V3 ok"),
                ("dmm_5va", "5V", "a_5v", "5V ok"),
                ("dmm_5vb", "5V", "b_5v", "5V ok"),
                ("dmm_5vc", "5V", "c_5v", "5V ok"),
                ("dmm_5vd", "5V", "d_5v", "5V ok"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
                ("ui_yesnodisplay", "Notify", "yesnodisplay", "Check all displays"),
            )
        )
        self["dmm"] = (  # This is indexed using position (1-N)
            None,
            ("dmm_3v3a", "dmm_5va"),
            ("dmm_3v3b", "dmm_5vb"),
            ("dmm_3v3c", "dmm_5vc"),
            ("dmm_3v3d", "dmm_5vd"),
        )
        self["dmm_lite"] = (  # This is indexed using position (1-N)
            None,
            ("dmm_5va",),
            ("dmm_5vb",),
            ("dmm_5vc",),
            ("dmm_5vd",),
        )
