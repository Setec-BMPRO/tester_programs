#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101x Final Test Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """RVMC101x Final Test Program."""

    limitdata = (
        libtester.LimitBoolean("ButtonOk", True, doc="Ok entered"),
        libtester.LimitBoolean("Zone4Pressed", True, doc="Button pressed"),
    )
    is_full = None  # False if 'Lite' version (no uC)

    def open(self):
        """Create the test program as a linear sequence."""
        super().configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.is_full = self.parameter != "LITE"
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("CanBus", self._step_canbus, self.is_full),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["dcs_vin"].output(12.0, output=True, delay=1.0)
        mes["ui_tabletscreen"]()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        # Tell user to push unit's button after clicking OK
        mes["ui_buttonpress"]()
        with dev["canreader"]:
            # Wait for the button press
            mes["zone4"](timeout=10)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        self["dcs_vin"] = tester.DCSource(self.physical_devices["DCS1"])
        self["can"] = self.physical_devices["CAN"]
        self["canreader"] = tester.CANReader(self["can"])
        self["decoder"] = share.can.PacketPropertyReader(
            canreader=self["canreader"], decoder=share.can.SwitchStatusDecoder()
        )

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
        """Create all Sensors."""
        sensor = tester.sensor
        self["ButtonPress"] = sensor.OkCan(  # Press the 'RET' button
            message=tester.translate("rvmc101_final", "msgPressButton"),
            caption=tester.translate("rvmc101_final", "capPressButton"),
        )
        self["TabletScreen"] = sensor.YesNo(  # Is the screen on
            message=tester.translate("rvmc101_final", "msgTabletScreen?"),
            caption=tester.translate("rvmc101_final", "capTabletScreen"),
        )
        self["zone4"] = sensor.Keyed(self.devices["decoder"], "zone4")


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ui_buttonpress", "ButtonOk", "ButtonPress", ""),
                ("ui_tabletscreen", "Notify", "TabletScreen", ""),
                ("zone4", "Zone4Pressed", "zone4", "4 button pressed"),
            )
        )
