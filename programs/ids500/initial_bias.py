#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 Bias Initial Test Program."""

import tester

import share


class InitialBias(share.TestSequence):
    """IDS-500 Initial Bias Test Program."""

    limitdata = (
        tester.LimitLow("FixtureLock", 20),
        tester.LimitDelta("400V", 390, 410),
        tester.LimitBetween("Vcc", 12.8, 14.5),
        tester.LimitBetween("12V", 12.7, 13.49),
    )
    full_load = 1.2  # Must supply at least this much current

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_pwrup),
            tester.TestStep("Load", self._step_load),
        )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power up unit."""
        mes["dmm_lock"](timeout=5)
        # Power up internal IDS-500 for 400V rail
        dev["acsource"].output(voltage=240.0, output=True)
        self.measure(
            (
                "dmm_400V",
                "dmm_Vcc",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure NoLoad/FullLoad."""
        with tester.PathName("NoLoad"):
            dev["dcl_12V"].output(0.0, True)
            mes["dmm_12V"](timeout=5)
        with tester.PathName("FullLoad"):
            dev["dcl_12V"].output(self.full_load, delay=0.5)
            mes["dmm_12V"](timeout=5)


class Devices(share.Devices):
    """Bias Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcl_12V", tester.DCLoad, "DCL1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset(delay=2)
        self["discharge"].pulse()
        self["dcl_12V"].output(0.0, False)


class Sensors(share.Sensors):
    """Bias Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["lock"] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self["400V"] = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self["Vcc"] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self["12V"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)


class Measurements(share.Measurements):
    """Bias Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", ""),
                ("dmm_400V", "400V", "400V", ""),
                ("dmm_Vcc", "Vcc", "Vcc", ""),
                ("dmm_12V", "12V", "12V", ""),
            )
        )
