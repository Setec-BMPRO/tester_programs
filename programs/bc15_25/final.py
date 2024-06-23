#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""BC15/25 Final Test Program."""

import tester
import share
from . import config


class Final(share.TestSequence):
    """BC15/25 Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        self.ocp_nominal, limits = self.cfg.limits_final()
        Sensors.ocp_nominal = self.ocp_nominal
        self.configure(limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerOn", self._step_poweron),
            tester.TestStep("Load", self._step_loaded),
        )

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Power up the Unit and measure output with min load."""
        dev["dcl"].output(1.0, output=True)
        dev["acsource"].output(240.0, output=True)
        self.measure(
            (
                "ui_yesnopsmode",
                "vout_nl",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_loaded(self, dev, mes):
        """Load the Unit."""
        dev["dcl"].output(self.ocp_nominal - 1.0)
        self.measure(
            (
                "vout",
                "ocp",
                "ui_yesnochmode",
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
            ("acsource", tester.ACSource, "ACS"),
            ("dcl", tester.DCLoad, "DCL1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    ocp_nominal = None  # Nominal OCP point of unit

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vout"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        if self.parameter == "15":
            msg_psmode = tester.translate("bc15_final", "GoToPsMode")
            msg_chrg = tester.translate("bc15_final", "GoToChargeMode")
        else:
            msg_psmode = tester.translate("bc25_final", "GoToPsMode")
            msg_chrg = tester.translate("bc25_final", "GoToChargeMode")
        cap_psmode = tester.translate("bc15_25_final", "capPsMode")
        cap_chrg = tester.translate("bc15_25_final", "capChargeMode")
        self["yesnopsmode"] = sensor.YesNo(message=msg_psmode, caption=cap_psmode)
        self["yesnochmode"] = sensor.YesNo(message=msg_chrg, caption=cap_chrg)
        self["ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["vout"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(
                start=self.ocp_nominal - 1.0, stop=self.ocp_nominal + 2.0, step=0.1
            ),
            delay=0.2,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("vout_nl", "VoutNL", "vout", ""),
                ("vout", "Vout", "vout", ""),
                ("ui_yesnopsmode", "Notify", "yesnopsmode", ""),
                ("ui_yesnochmode", "Notify", "yesnochmode", ""),
                ("ocp", "OCP", "ocp", ""),
            )
        )
