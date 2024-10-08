#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd
"""SX-600 Final Test Program."""

import tester

import share
from . import config


class Final(share.TestSequence):
    """SX-600 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        self.cfg = config.Config
        limits = self.cfg.limits_final
        self.configure(limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("PowerOn", self._step_poweron),
            tester.TestStep("Load", self._step_load),
            tester.TestStep("Load115", self._step_load115),
        )

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Switch on unit at 240Vac, light load, not enabled."""
        dev["dcs_fixture"].output(self.cfg.part_detect, output=True)
        dev["dcs_disable_pwr"].output(self.cfg.disable_pwr, output=True)
        self.dcload((("dcl_5v", 0.0), ("dcl_12v", 0.1), ("dcl_24v", 0.1)), output=True)
        self.measure(("dmm_Iecoff", "dmm_FanOff"), timeout=5)
        dev["acsource"].output(240.0, output=True, delay=0.5)
        self.measure(("dmm_Iec", "dmm_5v", "dmm_12voff", "ui_YesNoGreen"), timeout=5)

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Enable all outputs and check that the LED goes blue."""
        dev["dcs_disable_pwr"].output(0.0)
        dev["rla_pwron"].set_on()
        self.measure(
            (
                "dmm_BrktLeft",
                "dmm_BrktRight",
                "dmm_FanOn",
                "ui_YesNoBlue",
                "dmm_5v",
                "dmm_PwrGood",
                "dmm_AcFail",
            ),
            timeout=10,
        )

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure loaded outputs and load regulation."""
        nl12v, nl24v = self.measure(
            (
                "dmm_12von",
                "dmm_24von",
            )
        ).readings
        self.dcload(
            (
                ("dcl_5v", 2.0),
                ("dcl_12v", self.cfg.ratings.v12.full * 0.95),
                ("dcl_24v", self.cfg.ratings.v24.full * 0.95),
            ),
            output=True,
        )
        self.measure(
            (
                "dmm_5vfl",
                "dmm_PwrGood",
                "dmm_AcFail",
            ),
            timeout=2,
        )
        fl12v, fl24v = self.measure(
            (
                "dmm_12vfl",
                "dmm_24vfl",
            )
        ).readings
        # Load regulation values in %
        mes["reg12v"].sensor.store(100 * (nl12v.value - fl12v.value) / nl12v.value)
        mes["reg24v"].sensor.store(100 * (nl24v.value - fl24v.value) / nl24v.value)
        self.measure(
            (
                "reg12v",
                "reg24v",
            )
        )

    @share.teststep
    def _step_load115(self, dev, mes):
        """115Vac step."""
        dev["acsource"].output(voltage=115.0, delay=0.5)
        self.measure(
            (
                "dmm_5vfl",
                "dmm_12vfl",
                "dmm_24vfl",
            ),
            timeout=5,
        )


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcs_disable_pwr", tester.DCSource, "DCS2"),
            ("dcs_fixture", tester.DCSource, "DCS3"),
            ("dcl_12v", tester.DCLoad, "DCL1"),
            ("dcl_5v", tester.DCLoad, "DCL2"),
            ("dcl_24v", tester.DCLoad, "DCL3"),
            ("rla_pwron", tester.Relay, "RLA1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl_12v"].output(10, delay=0.5)
        for load in ("dcl_12v", "dcl_5v", "dcl_24v"):
            self[load].output(0.0, False)
        for dcs in ("dcs_disable_pwr", "dcs_fixture"):
            self[dcs].output(0.0, False)
        self["rla_pwron"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oInpRes"] = sensor.Res(dmm, high=1, low=1, rng=1000000, res=1)
        self["oIec"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["o5v"] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self["o12v"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.0001)
        self["o24v"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.0001)
        self["oPwrGood"] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self["oAcFail"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self["oFanDet"] = sensor.Vdc(dmm, high=8, low=2, rng=100, res=0.01)
        self["oBrktLeft"] = sensor.Vdc(dmm, high=9, low=2, rng=100, res=0.01)
        self["oBrktRight"] = sensor.Vdc(dmm, high=10, low=2, rng=100, res=0.01)
        self["oMir12v"] = sensor.Mirror()
        self["oMir24v"] = sensor.Mirror()
        self["oYesNoGreen"] = sensor.YesNo(
            message=tester.translate("sx600_final", "IsLedGreen?"),
            caption=tester.translate("sx600_final", "capLedGreen"),
        )
        self["oYesNoBlue"] = sensor.YesNo(
            message=tester.translate("sx600_final", "IsLedBlue?"),
            caption=tester.translate("sx600_final", "capLedBlue"),
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("reg12v", "Reg12V", "oMir12v", ""),
                ("reg24v", "Reg24V", "oMir24v", ""),
                ("dmm_InpRes", "InRes", "oInpRes", ""),
                ("dmm_FanOff", "FanOff", "oFanDet", ""),
                ("dmm_FanOn", "FanOn", "oFanDet", ""),
                ("dmm_BrktLeft", "BracketDetect", "oBrktLeft", ""),
                ("dmm_BrktRight", "BracketDetect", "oBrktRight", ""),
                ("dmm_Iecoff", "IECoff", "oIec", ""),
                ("dmm_Iec", "IEC", "oIec", ""),
                ("dmm_5v", "5Vnl", "o5v", ""),
                ("dmm_12voff", "12Voff", "o12v", ""),
                ("dmm_12von", "12Vnl", "o12v", ""),
                ("dmm_24von", "24Vnl", "o24v", ""),
                ("dmm_PwrGood", "PGOOD", "oPwrGood", ""),
                ("dmm_AcFail", "ACFAIL", "oAcFail", ""),
                ("dmm_5vfl", "5Vfl", "o5v", ""),
                ("dmm_12vfl", "12Vfl", "o12v", ""),
                ("dmm_24vfl", "24Vfl", "o24v", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoBlue", "Notify", "oYesNoBlue", ""),
            )
        )
