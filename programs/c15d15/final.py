#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""C15D-15 Final Test Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """C15D-15 Final Test Program."""

    # Resistive loading during OCP
    iload = 1.0
    limitdata = (
        libtester.LimitPercent("Vout", 15.5, 2.0),
        libtester.LimitLow("VoutOverLoad", 5.0),
        libtester.LimitBetween("OCP", 1.0, 1.4),
        libtester.LimitLow("inOCP", 13.6),
    )

    def open(self):
        """Create the test program as a linear sequence."""
        Sensors.iload = self.iload
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("OverLoad", self._step_over_load),
            tester.TestStep("Recover", self._step_recover),
            tester.TestStep("PowerOff", self._step_power_off),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up with 12Vdc, measure output, check Green and Yellow leds."""
        dev["dcs_Input"].output(12.0, output=True)
        dev["dcl"].output(0.0, output=True)
        self.measure(
            (
                "dmm_Vout",
                "ui_YesNoGreen",
                "ui_YesNoYellowOff",
                "ui_NotifyYellow",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        with dev["rla_load"]:
            mes["ramp_OCP"](timeout=5)
        self.measure(
            (
                "ui_YesNoYellowOn",
                "dmm_Vout",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_over_load(self, dev, mes):
        """Measure output at over load condition."""
        dev["dcl"].output(1.18, output=True)
        mes["dmm_Voutol"](timeout=5)

    @share.teststep
    def _step_recover(self, dev, mes):
        """Recover from over load."""
        dev["dcl"].output(0.0)
        dev["dcs_Input"].output(0.0, delay=1)
        dev["dcs_Input"].output(12.0)
        mes["dmm_Vout"](timeout=5)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Input DC off and discharge."""
        dev["dcl"].output(1.0)
        dev["dcs_Input"].output(0.0, delay=2)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Input", tester.DCSource, "DCS2"),
            ("dcl", tester.DCLoad, "DCL5"),
            ("rla_load", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["dcs_Input"].output(0.0, False)
        self["dcl"].output(0.0, False)
        self["rla_load"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    # Resistive loading during OCP
    iload = 0.0

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oVout"] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self["oYesNoGreen"] = sensor.YesNo(
            message=tester.translate("c15d15_final", "IsPowerLedGreen?"),
            caption=tester.translate("c15d15_final", "capPowerLed"),
        )
        self["oYesNoYellowOff"] = sensor.YesNo(
            message=tester.translate("c15d15_final", "IsYellowLedOff?"),
            caption=tester.translate("c15d15_final", "capOutputLed"),
        )
        self["oNotifyYellow"] = sensor.Notify(
            message=tester.translate("c15d15_final", "WatchYellowLed"),
            caption=tester.translate("c15d15_final", "capOutputLed"),
        )
        self["oYesNoYellowOn"] = sensor.YesNo(
            message=tester.translate("c15d15_final", "IsYellowLedOn?"),
            caption=tester.translate("c15d15_final", "capOutputLed"),
        )
        self["oOCP"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["oVout"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=0.0, stop=0.5, step=0.05),
            delay=0.2,
        )
        self["oOCP"].on_read = lambda value: value + self.iload


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_Vout", "Vout", "oVout", ""),
                ("dmm_Voutol", "VoutOverLoad", "oVout", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoYellowOff", "Notify", "oYesNoYellowOff", ""),
                ("ui_NotifyYellow", "Notify", "oNotifyYellow", ""),
                ("ui_YesNoYellowOn", "Notify", "oYesNoYellowOn", ""),
                ("ramp_OCP", "OCP", "oOCP", ""),
            )
        )
