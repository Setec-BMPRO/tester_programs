#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd.
"""BC60 Final Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """Final Test Program."""

    final_limits = (
        libtester.LimitBoolean("ButtonOk", True, doc="Ok entered"),
        libtester.LimitDelta("VoutNL", 12.0, 1.5, doc="Output at no load"),
        libtester.LimitBetween("Vout", 14.0, 15.0, doc="Output at charge"),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.final_limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Load", self._step_load),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit."""
        dev["dcs_sec"].output(13.0, output=True)
        dev["dcl_Vout"].output(1.5, output=True)
        mes["VoutNL"](timeout=5)
        mes["WatchLEDs"]()  # Tell user to watch unit's LEDs
        dev["acsource"].output(voltage=240.0, output=True, delay=0.5)
        mes["Display"]()  # Did unit's LEDs work properly?

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure output."""
        dcl = dev["dcl_Vout"]
        for load in range(10, 61, 10):
            with tester.PathName("{0}A".format(load)):
                dcl.output(load, delay=0.5)
                mes["Vout"](timeout=5)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcs_sec", tester.DCSource, "DCS1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcl_Vout"] = tester.DCLoadParallel(
            (
                (tester.DCLoad(self.physical_devices["DCL1"]), 10),
                (tester.DCLoad(self.physical_devices["DCL3"]), 10),
            )
        )

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl_Vout"].output(10.0, output=True, delay=0.5)
        self["dcl_Vout"].output(0.0)
        self["dcs_sec"].output(0.0, output=False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["Vout"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self["Vout"].doc = "Output"
        self["LEDs"] = sensor.OkCan(  # Watch LEDs after pressing Ok
            message=tester.translate("bc60_final", "msgLEDs"),
            caption=tester.translate("bc60_final", "capLEDs"),
        )
        self["LEDs"].doc = "Operator notification"
        self["Display"] = sensor.YesNo(  # Did display work ok?
            message=tester.translate("bc60_final", "msgDisplay"),
            caption=tester.translate("bc60_final", "capDisplay"),
        )
        self["Display"].doc = "Operator response"


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("VoutNL", "VoutNL", "Vout", ""),
                ("WatchLEDs", "ButtonOk", "LEDs", ""),
                ("Display", "Notify", "Display", ""),
                ("Vout", "Vout", "Vout", ""),
            )
        )
