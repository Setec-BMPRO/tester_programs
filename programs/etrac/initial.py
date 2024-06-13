#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""ETrac-II Initial Test Program."""

import libtester
import serial
import tester

import share
from . import arduino


class Initial(share.TestSequence):
    """ETrac-II Initial Test Program."""

    limitdata = (
        libtester.LimitBetween("Vin", 12.9, 13.1),
        libtester.LimitBetween("Vin2", 10.8, 12.8),
        libtester.LimitBetween("5V", 4.95, 5.05),
        libtester.LimitBetween("5Vusb", 4.75, 5.25),
        libtester.LimitBetween("Vbat", 8.316, 8.484),
        libtester.LimitRegExp("Reply", r"^OK$"),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Load", self._step_load),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input DC and measure voltages."""
        dev["ard"].open()
        dev["rla_SS"].set_on()
        dev["dcs_Vin"].output(13.0, output=True)
        self.measure(
            (
                "dmm_Vin",
                "dmm_Vin2",
                "dmm_5V",
            ),
            timeout=10,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the PIC device."""
        with dev["rla_Prog"]:
            mes["pgm_etrac2"]()

    @share.teststep
    def _step_load(self, dev, mes):
        """Load and measure voltages."""
        self.measure(
            (
                "dmm_5Vusb",
                "dmm_Vbat",
            ),
            timeout=10,
        )
        dev["rla_BattLoad"].set_on()
        mes["dmm_Vbat"](timeout=10)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Vin", tester.DCSource, "DCS1"),
            ("dcs_Vcom", tester.DCSource, "DCS2"),
            ("rla_SS", tester.Relay, "RLA1"),
            ("rla_Prog", tester.Relay, "RLA2"),
            ("rla_BattLoad", tester.Relay, "RLA3"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port("019883", "ARDUINO")
        self["ard"] = arduino.Arduino(ard_ser)
        # Switch on power to fixture circuits
        self["dcs_Vcom"].output(12.0, output=True, delay=2)
        self.add_closer(lambda: self["dcs_Vcom"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["ard"].close()
        self["dcs_Vin"].output(0.0, False)
        for rla in ("rla_SS", "rla_Prog", "rla_BattLoad"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oVin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self["oVin2"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self["o5V"] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self["o5Vusb"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self["oVbat"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        # Arduino sensor
        ard = self.devices["ard"]
        self["pgmEtrac2"] = sensor.Keyed(ard, "PGM_ETRAC2")


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_Vin", "Vin", "oVin", ""),
                ("dmm_Vin2", "Vin2", "oVin2", ""),
                ("dmm_5V", "5V", "o5V", ""),
                ("dmm_5Vusb", "5Vusb", "o5Vusb", ""),
                ("dmm_Vbat", "Vbat", "oVbat", ""),
                ("pgm_etrac2", "Reply", "pgmEtrac2", ""),
            )
        )
