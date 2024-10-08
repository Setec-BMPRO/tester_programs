#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""TS3020H Final Test Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """TS3020H Final Test Program."""

    limitdata = (
        libtester.LimitLow("12Voff", 0.5),
        libtester.LimitBetween("12V", 13.7, 13.9),
        libtester.LimitBetween("12Vfl", 13.43, 13.9),
        libtester.LimitBetween("OCP", 25.0, 30.0),
        libtester.LimitLow("inOCP", 13.3),
    )

    def open(self):
        """Create the test program as a linear sequence."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("FuseCheck", self._step_fuse_check),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("FullLoad", self._step_full_load),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("Poweroff", self._step_power_off),
        )

    @share.teststep
    def _step_fuse_check(self, dev, mes):
        """Powerup with output fuse removed, measure output off."""
        mes["ui_NotifyStart"]()
        dev["acsource"].output(240.0, output=True, delay=0.5)
        self.measure(("dmm_12Voff", "ui_YesNoRed"), timeout=5)
        dev["acsource"].output(0.0, delay=0.5)
        mes["ui_NotifyFuse"]()

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Switch on unit at 240Vac, measure output voltages at no load."""
        dev["acsource"].output(240.0, delay=0.5)
        self.measure(("dmm_12V", "ui_YesNoGreen"), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        with tester.PathName("240V"):
            dev["dcl"].output(25.0, output=True)
            mes["dmm_12Vfl"](timeout=5)
        with tester.PathName("90V"):
            dev["acsource"].output(90.0, delay=1.0)
            mes["dmm_12Vfl"](timeout=5)
            dev["acsource"].output(240.0, delay=1.0)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes["ramp_OCP"]()

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Switch off unit, measure output voltage."""
        dev["acsource"].output(0.0, delay=0.5)
        self.measure(("ui_NotifyMains", "dmm_12Voff", "ui_YesNoOff"), timeout=5)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcl"] = tester.DCLoadParallel(
            (
                (tester.DCLoad(self.physical_devices["DCL1"]), 12.5),
                (tester.DCLoad(self.physical_devices["DCL2"]), 12.5),
            )
        )

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["o12V"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["oNotifyStart"] = sensor.Notify(
            message=tester.translate("ts3020h_final", "RemoveFuseSwitchOn"),
            caption=tester.translate("ts3020h_final", "capSwitchOn"),
        )
        self["oNotifyFuse"] = sensor.Notify(
            message=tester.translate("ts3020h_final", "ReplaceFuse"),
            caption=tester.translate("ts3020h_final", "capReplaceFuse"),
        )
        self["oNotifyMains"] = sensor.Notify(
            message=tester.translate("ts3020h_final", "SwitchOff"),
            caption=tester.translate("ts3020h_final", "capSwitchOff"),
        )
        self["oYesNoRed"] = sensor.YesNo(
            message=tester.translate("ts3020h_final", "IsRedLedOn?"),
            caption=tester.translate("ts3020h_final", "capRedLed"),
        )
        self["oYesNoGreen"] = sensor.YesNo(
            message=tester.translate("ts3020h_final", "IsGreenLedOn?"),
            caption=tester.translate("ts3020h_final", "capGreenLed"),
        )
        self["oYesNoOff"] = sensor.YesNo(
            message=tester.translate("ts3020h_final", "AreAllLightsOff?"),
            caption=tester.translate("ts3020h_final", "capAllOff"),
        )
        self["oOCP"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["o12V"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=24.5, stop=31.0, step=0.5),
            delay=3.0,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_12Voff", "12Voff", "o12V", ""),
                ("dmm_12V", "12V", "o12V", ""),
                ("dmm_12Vfl", "12Vfl", "o12V", ""),
                ("ramp_OCP", "OCP", "oOCP", ""),
                ("ui_NotifyStart", "Notify", "oNotifyStart", ""),
                ("ui_NotifyFuse", "Notify", "oNotifyFuse", ""),
                ("ui_NotifyMains", "Notify", "oNotifyMains", ""),
                ("ui_YesNoRed", "Notify", "oYesNoRed", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoOff", "Notify", "oYesNoOff", ""),
            )
        )
