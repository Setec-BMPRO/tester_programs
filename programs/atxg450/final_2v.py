#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd.
"""ATXG-450-2V Final Test Program."""

import tester

import share


class Final2V(share.TestSequence):
    """ATXG-450-2V Final Test Program."""

    limitdata = (
        tester.LimitBetween("5Vsb", 4.845, 5.202),
        tester.LimitLow("5Vsbinocp", 4.70),
        tester.LimitBetween("5Vsbocp", 2.6, 4.0),
        tester.LimitLow("24Voff", 0.5),
        tester.LimitBetween("24Von", 23.75, 26.25),
        tester.LimitLow("24Vinocp", 22.8),
        tester.LimitBetween("24Vocp", 18.0, 24.0),
        tester.LimitLow("12Voff", 0.5),
        tester.LimitBetween("12Von", 11.685, 12.669),
        tester.LimitLow("12Vinocp", 10.0),
        tester.LimitBetween("12Vocp", 20.5, 26.0),
        tester.LimitLow("5Voff", 0.5),
        tester.LimitBetween("5Von", 4.725, 5.4075),
        tester.LimitLow("5Vinocp", 4.75),
        tester.LimitBetween("5Vocp", 20.5, 26.0),
        tester.LimitLow("3V3off", 0.5),
        tester.LimitBetween("3V3on", 3.1825, 3.4505),
        tester.LimitLow("3V3inocp", 3.20),
        tester.LimitBetween("3V3ocp", 17.0, 26.0),
        tester.LimitHigh("-12Voff", -0.5),
        tester.LimitBetween("-12Von", -12.48, -11.52),
        tester.LimitLow("PwrGoodOff", 0.5),
        tester.LimitHigh("PwrGoodOn", 4.5),
        tester.LimitHigh("PwrFailOff", 4.5),
        tester.LimitLow("PwrFailOn", 0.5),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("SwitchOn", self._step_switch_on),
            tester.TestStep("FullLoad", self._step_full_load),
            tester.TestStep("OCP24", self._step_ocp24),
            tester.TestStep("OCP12", self._step_ocp12),
            tester.TestStep("OCP5", self._step_ocp5),
            tester.TestStep("OCP3", self._step_ocp3),
            tester.TestStep("OCP5sb", self._step_ocp5sb),
            tester.TestStep("PowerFail", self._step_power_fail),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Switch on unit at 240Vac, not enabled, measure output voltages."""
        dev["dcs_PsOn"].output(12.0, output=True, delay=0.1)
        dev["acsource"].output(240.0, output=True, delay=0.5)
        self.measure(
            (
                "dmm_5Vsb",
                "ui_YesNoGreen",
                "dmm_24Voff",
                "dmm_12Voff",
                "dmm_5Voff",
                "dmm_3V3off",
                "dmm_n12Voff",
                "dmm_PwrGoodOff",
                "dmm_PwrFailOff",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_switch_on(self, dev, mes):
        """Enable outputs, measure."""
        self.dcload((("dcl_12V", 1.0), ("dcl_24V", 1.0), ("dcl_5V", 1.0)))
        dev["dcs_PsOn"].output(0.0, output=True, delay=0.1)
        self.measure(
            (
                "dmm_24Von",
                "dmm_12Von",
                "dmm_5Von",
                "dmm_3V3on",
                "dmm_n12Von",
                "dmm_PwrGoodOn",
                "dmm_PwrFailOn",
                "ui_YesNoFan",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        self.dcload(
            (
                ("dcl_5Vsb", 1.0),
                ("dcl_24V", 5.0),
                ("dcl_5V", 10.0),
                ("dcl_12V", 10.0),
                ("dcl_3V3", 10.0),
            ),
            delay=0.5,
        )
        self.measure(
            (
                "dmm_5Vsb",
                "dmm_24Von",
                "dmm_12Von",
                "dmm_5Von",
                "dmm_3V3on",
                "dmm_n12Von",
                "dmm_PwrGoodOn",
                "dmm_PwrFailOn",
            ),
            timeout=5,
        )
        # Drop back to minimum loads
        self.dcload(
            (
                ("dcl_5Vsb", 0.0),
                ("dcl_24V", 0.5),
                ("dcl_12V", 0.5),
                ("dcl_5V", 0.5),
                ("dcl_3V3", 0.0),
            )
        )

    @share.teststep
    def _step_ocp24(self, dev, mes):
        """Measure 24V OCP point."""
        dev["dcl_24V"].binary(0.0, 17.5, 5.0)
        mes["ramp_24Vocp"]()
        dev["dcl_24V"].output(0.5)
        self._restart(dev)

    @share.teststep
    def _step_ocp12(self, dev, mes):
        """Measure 12V OCP point."""
        dev["dcl_12V"].binary(0.0, 19.5, 1.0)
        mes["ramp_12Vocp"]()
        dev["dcl_12V"].output(0.5)
        self._restart(dev)

    @share.teststep
    def _step_ocp5(self, dev, mes):
        """Measure 5V OCP point."""
        dev["dcl_5V"].binary(0.0, 19.5, 1.0)
        mes["ramp_5Vocp"]()
        dev["dcl_5V"].output(0.5)
        self._restart(dev)

    @share.teststep
    def _step_ocp3(self, dev, mes):
        """Measure 3V3 OCP point."""
        dev["dcl_3V3"].binary(0.0, 16.5, 5.0)
        mes["ramp_3V3ocp"]()
        dev["dcl_3V3"].output(0.5)
        self._restart(dev)

    @share.teststep
    def _step_ocp5sb(self, dev, mes):
        """Measure 5Vsb OCP point."""
        dev["dcl_5Vsb"].binary(0.0, 2.1, 1.0)
        mes["ramp_5Vsbocp"]()
        dev["dcl_5Vsb"].output(0.0)
        self._restart(dev)

    @share.teststep
    def _step_power_fail(self, dev, mes):
        """Switch off unit, measure."""
        dev["acsource"].output(0.0, output=False, delay=0.5)
        mes["dmm_PwrFailOff"]()

    def _restart(self, dev):
        """Re-Start unit after OCP by using PS_ON."""
        dev["dcs_PsOn"].output(12.0, output=True, delay=0.5)
        dev["dcs_PsOn"].output(0.0, delay=2.0)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            # This DC Source controls the PS_ON signal (12V == Unit OFF)
            ("dcs_PsOn", tester.DCSource, "DCS2"),
            ("dcl_24V", tester.DCLoad, "DCL1"),
            ("dcl_12V", tester.DCLoad, "DCL2"),
            ("dcl_5V", tester.DCLoad, "DCL3"),
            ("dcl_3V3", tester.DCLoad, "DCL4"),
            ("dcl_5Vsb", tester.DCLoad, "DCL5"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        for ld in ("dcl_24V", "dcl_12V", "dcl_5V", "dcl_3V3", "dcl_5Vsb"):
            self[ld].output(0.0, False)
        self["dcs_PsOn"].output(0.0, output=False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oIec"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["o24V"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["o12V"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["o5V"] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self["o3V3"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["o5Vsb"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.0001)
        self["on12V"] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self["oPwrGood"] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self["oPwrFail"] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self["oYesNoGreen"] = sensor.YesNo(
            message=tester.translate("atxg450_2v_final", "IsSwitchGreen?"),
            caption=tester.translate("atxg450_2v_final", "capSwitchGreen"),
        )
        self["oYesNoFan"] = sensor.YesNo(
            message=tester.translate("atxg450_2v_final", "IsFanRunning?"),
            caption=tester.translate("atxg450_2v_final", "capFan"),
        )
        self["o24Vocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_24V"],
            sensor=self["o24V"],
            detect_limit=self.limits["24Vinocp"],
            ramp_range=sensor.RampRange(start=17.5, stop=24.5, step=0.1),
            delay=0.1,
        )
        self["o12Vocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_12V"],
            sensor=self["o12V"],
            detect_limit=self.limits["12Vinocp"],
            ramp_range=sensor.RampRange(start=19.5, stop=26.5, step=0.1),
            delay=0.1,
        )
        self["o5Vocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_5V"],
            sensor=self["o5V"],
            detect_limit=self.limits["5Vinocp"],
            ramp_range=sensor.RampRange(start=19.5, stop=26.5, step=0.1),
            delay=0.1,
        )
        self["o3V3ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_3V3"],
            sensor=self["o3V3"],
            detect_limit=self.limits["3V3inocp"],
            ramp_range=sensor.RampRange(start=16.5, stop=26.5, step=0.1),
            delay=0.1,
        )
        self["o5Vsbocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_5Vsb"],
            sensor=self["o5Vsb"],
            detect_limit=self.limits["5Vsbinocp"],
            ramp_range=sensor.RampRange(start=2.1, stop=4.7, step=0.1),
            delay=0.1,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_5Vsb", "5Vsb", "o5Vsb", ""),
                ("dmm_24Voff", "24Voff", "o24V", ""),
                ("dmm_12Voff", "12Voff", "o12V", ""),
                ("dmm_5Voff", "5Voff", "o5V", ""),
                ("dmm_3V3off", "3V3off", "o3V3", ""),
                ("dmm_n12Voff", "-12Voff", "on12V", ""),
                ("dmm_24Von", "24Von", "o24V", ""),
                ("dmm_12Von", "12Von", "o12V", ""),
                ("dmm_5Von", "5Von", "o5V", ""),
                ("dmm_3V3on", "3V3on", "o3V3", ""),
                ("dmm_n12Von", "-12Von", "on12V", ""),
                ("dmm_PwrFailOff", "PwrFailOff", "oPwrFail", ""),
                ("dmm_PwrGoodOff", "PwrGoodOff", "oPwrGood", ""),
                ("dmm_PwrFailOn", "PwrFailOn", "oPwrFail", ""),
                ("dmm_PwrGoodOn", "PwrGoodOn", "oPwrGood", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoFan", "Notify", "oYesNoFan", ""),
                ("ramp_24Vocp", "24Vocp", "o24Vocp", ""),
                ("ramp_12Vocp", "12Vocp", "o12Vocp", ""),
                ("ramp_5Vocp", "5Vocp", "o5Vocp", ""),
                ("ramp_3V3ocp", "3V3ocp", "o3V3ocp", ""),
                ("ramp_5Vsbocp", "5Vsbocp", "o5Vsbocp", ""),
            )
        )
