#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Final Test Program."""

import tester
import share

from . import display


class Final(share.TestSequence):

    """RVMD50 Final Test Program."""

    vin_set = 12.0  # Input voltage to power the unit
    start_delay = 5.0  # Start up delay timer
    limitdata = (  # Test Limits
        tester.LimitBoolean("PagePressed", True, doc="Button pressed"),
    )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Display", self._step_display),
            tester.TestStep("Buttons", self._step_buttons),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["dcs_vin"].output(self.vin_set, output=True, delay=self.start_delay)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display test pattern & backlight."""
        with dev["display"]:
            mes["YesNoDisplayOk"](timeout=5)

    @share.teststep
    def _step_buttons(self, dev, mes):
        """Test the Buttons."""
        mes["OkCanButtonPress"]()
        with dev["canreader"]:
            mes["PageButton"](timeout=10)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        self["dcs_vin"] = tester.DCSource(self.physical_devices["DCS1"])
        self["can"] = self.physical_devices["_CAN"]
        self["canreader"] = tester.CANReader(self["can"])
        self["decoder"] = share.can.PacketPropertyReader(
            canreader=self["canreader"], decoder=share.can.DeviceStatusDecoder()
        )
        self["display"] = display.DisplayControl(self["can"])

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["canreader"].stop()
        self["can"].rvc_mode = False
        self["dcs_vin"].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        sensor = tester.sensor
        self["YesNoDisplay"] = sensor.YesNo(
            message=tester.translate("rvmd50", "DisplayCheck?"),
            caption=tester.translate("rvmd50", "capDisplayCheck"),
        )
        self["YesNoDisplay"].doc = "Operator input"
        self["OkCanButtonPress"] = sensor.OkCan(  # Press the 'Page' button
            message=tester.translate("rvmd50_final", "msgPressButton"),
            caption=tester.translate("rvmd50_final", "capPressButton"),
        )
        self["PageButton"] = sensor.Keyed(self.devices["decoder"], "page")


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("YesNoDisplayOk", "Notify", "YesNoDisplay", "Button on"),
                ("OkCanButtonPress", "Notify", "OkCanButtonPress", ""),
                ("PageButton", "PagePressed", "PageButton", "Page button pressed"),
            )
        )
