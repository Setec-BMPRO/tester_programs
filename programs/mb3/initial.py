#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Initial Program."""

import pathlib

import libtester
import tester

import share
from . import config


class Initial(share.TestSequence):
    """MB3 Initial Test Program."""

    limitdata = (
        libtester.LimitDelta("Vaux", config.vaux, 0.5),
        libtester.LimitPercent("5V", 5.0, 1.0),
        libtester.LimitDelta("Vbat", 14.6, 0.3),
    )

    def open(self):
        """Create the test program as a linear sequence."""
        Devices.fixture = self.fixture
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerOn", self._step_power_on),
            tester.TestStep("PgmAVR", self.devices["program_avr"].program),
            tester.TestStep("Output", self._step_output),
        )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        dev["dcs_vaux"].output(config.vaux, output=True, delay=0.5)
        self.measure(("dmm_vaux", "dmm_5v"), timeout=5)
        dev["rla_switch"].monostable(delay=0.5)
        dev["rla_trigger"].pulse(0.1)
        dev["rla_switch"].ftdi()

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output of the unit."""
        mes["dmm_vbat"](timeout=5)


class Devices(share.Devices):
    """Devices."""

    fixture = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vaux", tester.DCSource, "DCS2"),
            ("dcs_vfix", tester.DCSource, "DCS3"),
            ("rla_switch", tester.Relay, "RLA1"),
            ("rla_trigger", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        sw = self["rla_switch"]
        sw.monostable = sw.set_on
        sw.ftdi = sw.set_off
        # Serial port for the ATtiny406. Used by programmer and comms module.
        avr_port = self.port("AVR")
        # ATtiny406 device programmer
        self["program_avr"] = share.programmer.AVR(
            avr_port,
            pathlib.Path(__file__).parent / config.sw_image,
            fuses=config.fuses,
        )
        # Apply power to fixture circuits.
        self["dcs_vfix"].output(12.0, output=True)
        self.add_closer(lambda: self["dcs_vfix"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["dcs_vaux"].output(0.0, False)
        for rla in (
            "rla_switch",
            "rla_trigger",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vaux"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["5V"] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self["vbat"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vaux", "Vaux", "vaux", "Aux input ok"),
                ("dmm_5v", "5V", "5V", "5V ok"),
                ("dmm_vbat", "Vbat", "vbat", "Battery output ok"),
            )
        )
