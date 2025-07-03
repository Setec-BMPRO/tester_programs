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

    _limits = (
        libtester.LimitDelta("Vbat", 12.0, 0.5, doc="Battery input present"),
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
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        dev["dcs_vbat"].output(12.0, True)
        print("**********************************Applied 12Vdc to TRS-BT2")

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        mes["JLink"]()
        print("**********************************Programmed")

    @share.teststep
    def _step_operation(self, dev, mes):
        """Test the operation of LEDs."""
        trsbts = dev["trsbts"]
        trsbts.open()
        # Using device RESET results in sporadic duplicate startup banners
        # So, it's faster to just power cycle, than untangle the crappy console...
        dev["dcs_vbat"].output(0.0, delay=0.5)
        trsbts.reset_input_buffer()
        dev["dcs_vbat"].output(12.0)
        trsbts.initialise(self.config.hw_version, self.uuts[0].sernum)
        print("**********************************Initialized")


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
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
        self["rla_reset"].set_off()
        self["rla_boot"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
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
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
