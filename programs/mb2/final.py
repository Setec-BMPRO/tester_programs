#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""MB2 Final Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """MB2 Final Test Program."""

    vstart = 12.9
    vstop = 9.1

    limitdata = (
        libtester.LimitBetween("Vin", 9.0, 13.0),
        libtester.LimitPercent("Vout", 14.4, 3.0),
    )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (tester.TestStep("PowerOn", self._step_power_on),)

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Power up unit."""
        dev["dcs_vin"].output(self.vstart, True, delay=0.5)
        dev["dcl_vout"].output(0.1, True)
        self.measure(("dmm_vin", "ui_yesnolight", "dmm_vout"), timeout=5)
        dev["dcs_vin"].output(self.vstop)
        self.measure(
            (
                "dmm_vin",
                "ui_yesnooff",
            ),
            timeout=5,
        )


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("dcl_vout", tester.DCLoad, "DCL1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["dcs_vin"].output(0.0, False)
        self["dcl_vout"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vin"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["vout"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["yesnolight"] = sensor.YesNo(
            message=tester.translate("mb2_final", "IsLightOn?"),
            caption=tester.translate("mb2_final", "capLight"),
        )
        self["yesnooff"] = sensor.YesNo(
            message=tester.translate("mb2_final", "IsLightOff?"),
            caption=tester.translate("mb2_final", "capLight"),
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_vin", "Vin", "vin", ""),
                ("dmm_vout", "Vout", "vout", ""),
                ("ui_yesnolight", "Notify", "yesnolight", ""),
                ("ui_yesnooff", "Notify", "yesnooff", ""),
            )
        )
