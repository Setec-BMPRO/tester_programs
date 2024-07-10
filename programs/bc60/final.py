#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd.
"""BC60 Final Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """Final Test Program."""

    limits = (
        libtester.LimitDelta("VoutNL", 13.55, 0.20, doc="Output at no load"),
        libtester.LimitBetween("Vout", 12.98, 13.75, doc="Output with load"),
        libtester.LimitLow("inOCP", 12.98, doc="OCP active"),
        libtester.LimitBetween("OCPLoad", 20.0, 25.0, doc="OCP point"),
    )
#            "FullLoad": 20.1,
#            "OCPrampLoad": (20.0, 25.5),

    def open(self):
        """Prepare for testing."""
        self.configure(self.limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("FullLoad", self._step_full_load),
            tester.TestStep("OCP", self._step_ocp),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit."""
        dev["acsource"].output(voltage=240.0, output=True, delay=0.5)
        dev["dcl_Vout"].output(0.1, output=True)
        mes["VoutNL"](timeout=5)
        mes["VoutNL"](timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        mes["YesNoGreen"]()
        self.dcload(
            (
                ("dcl_Vout", self.limitdata[self.parameter]["FullLoad"]),
            )
        )
        mes["Vout"](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes["OCPLoad"]()
        dev["dcl_Vout"].output(0.0)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
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


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["Vout"] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self["Vout"].doc = "Output"


        self["YesNoGreen"] = sensor.YesNo(
            message=tester.translate("bc60_final", "IsGreenFlash?"),
            caption=tester.translate("bc60_final", "capLedGreen"),
        )
        self["YesNoGreen"].doc = "Operator response"
        ocp_start, ocp_stop = Final.limitdata[self.parameter]["OCPrampLoad"]
        self["OCPLoad"] = sensor.Ramp(
            stimulus=self.devices["dcl_Vout"],
            sensor=self["Vout"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=ocp_start, stop=ocp_stop, step=0.05),
            delay=0.1,
        )
        self["OCPLoad"].doc = "Load OCP point"


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("VoutNL", "VoutNL", "Vout", ""),
                ("Vout", "Vout", "Vout", ""),
                ("OCPLoad", "OCPLoad", "OCPLoad", ""),
                ("YesNoGreen", "Notify", "YesNoGreen", "Green LED flashing"),
            )
        )
