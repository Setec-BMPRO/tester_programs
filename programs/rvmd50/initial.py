#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Initial Test Program.

Shares the test fixture with the RVView/JDisplay program.

"""

import pathlib

from attrs import define, field
import libtester
import tester

import share
from . import config, display


class Initial(share.TestSequence):
    """RVMD50 Initial Test Program."""

    vin_set = 8.1
    testlimits = (
        libtester.LimitBetween("Vin", 7.0, 8.0, doc="Input voltage present"),
        libtester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        libtester.LimitLow("BkLghtOff", 0.5, doc="Backlight off"),
        libtester.LimitBetween("BkLghtOn", 2.5, 3.5, doc="Backlight on"),
    )

    def open(self):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        Devices.fixture = self.fixture
        Devices.sw_image = Sensors.sw_image = self.cfg.sw_image
        self.configure(self.testlimits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Display", self._step_display),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        dev["rla_reset"].set_on()
        dev["rla_watchdog_disable"].set_on()
        dev["dcs_vin"].output(self.vin_set, output=True)
        self.measure(("dmm_vin", "dmm_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        if self.parameter == "NXP":
            dev["program_arm"].program()  # A device
        else:
            mes["JLink"]()  # A measurement

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD and Backlight."""
        dev["rla_reset"].pulse(0.1, delay=5)
        mes["dmm_bklghtoff"](timeout=5)
        with dev["display"]:
            self.measure(("YesNoDisplayOk", "dmm_bklghton"), timeout=5)


@define
class LatchingRelay:
    """A latching relay, with 'on' and 'off' drive lines."""

    rla_on = field()
    rla_off = field()
    _pulse_time = field(init=False, default=0.01)

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

    fixture = None
    sw_image = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_rst", tester.DCSource, "DCS1"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("rla_rst_on", tester.Relay, "RLA1"),
            ("rla_rst_off", tester.Relay, "RLA2"),
            ("rla_boot", tester.Relay, "RLA3"),
            ("rla_watchdog_disable", tester.Relay, "RLA4"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["rla_reset"] = LatchingRelay(self["rla_rst_on"], self["rla_rst_off"])
        # ARM device programmer
        self["program_arm"] = share.programmer.ARM(
            share.config.Fixture.port(self.fixture, "ARM"),
            pathlib.Path(__file__).parent / self.sw_image,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        self["can"] = self.physical_devices["CAN"]
        self["display"] = display.DisplayControl(self["can"])
        self["dcs_rst"].output(8.0, True)  # Fixture RESET circuit
        self.add_closer(lambda: self["dcs_rst"].output(0.0, output=False))

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True

    def reset(self):
        """Test run has stopped."""
        self["can"].rvc_mode = False
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_watchdog_disable"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["vin"].doc = "X1"
        self["3v3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3v3"].doc = "U1 output"
        self["bklght"] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self["bklght"].doc = "Across backlight"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("atsamc21e17"),
            pathlib.Path(__file__).parent / self.sw_image,
        )
        self["YesNoDisplay"] = sensor.YesNo(
            message=tester.translate("rvmd50", "DisplayCheck?"),
            caption=tester.translate("rvmd50", "capDisplayCheck"),
        )
        self["YesNoDisplay"].doc = "Operator input"


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
                ("YesNoDisplayOk", "Notify", "YesNoDisplay", "Button on"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
