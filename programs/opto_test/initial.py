#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""JControl/Trek2/Trek3 Initial Test Program."""

import pathlib

import libtester
import serial
import tester

import share
from . import config
from . import console
import time


class Initial(share.TestSequence):
    """Trek2/JControl Initial Test Program."""

    _limits = (
        libtester.LimitDelta("Vin", 12.0, 0.5, doc="Input voltage present"),
    )

    def open(self):
        """Create the test program as a linear sequence."""
        self.config = config.get(self.parameter)
        Devices.sw_image = self.config.sw_image
        self.configure(self._limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self.devices["programmer"].program),
            tester.TestStep("TestArm", self._step_test_arm),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["dcs_vin"].output(self.config.vin_set, output=True)
        print("**********************************Applied 12Vdc to Trek2/Trek3/JControl")

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        print("**********************************Programmed")
        dev["arm"].open()
        dev["arm"].brand(self.config.hw_version, self.uuts[0].sernum, dev["rla_reset"])
        print("**********************************Initialized")



class Devices(share.Devices):
    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS3"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        arm_port = self.port("ARM")
        self["programmer"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_image,
            crpmode=False,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        # Direct Console driver
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        self["arm"] = console.DirectConsole(arm_ser)

    def reset(self):
        """Reset instruments."""
        self["arm"].close()
        self["dcs_vin"].output(0.0, output=False)
        for rla in ("rla_reset", "rla_boot"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        arm = self.devices["arm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "X207"


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", "Input voltage"),
            )
        )
