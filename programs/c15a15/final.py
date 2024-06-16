#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""C15A-15 Final Test Program."""

import libtester
import tester

import share


class Final(share.TestSequence):
    """C15A-15 Final Test Program."""

    # Resistive loading during OCP
    iload = 1.0
    limitdata = (
        libtester.LimitDelta("Vout", 15.5, 0.3),
        libtester.LimitLow("Voutfl", 5.0),
        libtester.LimitBetween("OCP", 1.0, 1.4),
        libtester.LimitLow("inOCP", 13.6),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Sensors.iload = self.iload
        super().configure(self.limitdata, Devices, Sensors, Measurements)
        super().open(uut)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("FullLoad", self._step_full_load),
            tester.TestStep("PowerOff", self._step_power_off),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """
        Power up with 240Vac, measure output, check Green and Yellow leds.
        """
        dev["acsource"].output(240.0, output=True, delay=0.5)
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
        """Measure OCP."""
        with dev["rla_load"]:
            mes["ramp_OCP"]()
        self.measure(
            (
                "ui_YesNoYellowOn",
                "dmm_Vout",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure output at full load and after recovering."""
        dev["dcl"].output(1.31, output=True)
        mes["dmm_Voutfl"](timeout=5)
        dev["dcl"].output(0.0)
        mes["dmm_Vout"](timeout=5)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Input AC off and discharge."""
        dev["dcl"].output(1.0)
        dev["acsource"].output(0.0, delay=2)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcl", tester.DCLoad, "DCL5"),
            ("rla_load", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
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
            message=tester.translate("c15a15_final", "IsPowerLedGreen?"),
            caption=tester.translate("c15a15_final", "capPowerLed"),
        )
        self["oYesNoYellowOff"] = sensor.YesNo(
            message=tester.translate("c15a15_final", "IsYellowLedOff?"),
            caption=tester.translate("c15a15_final", "capOutputLed"),
        )
        self["oNotifyYellow"] = sensor.Notify(
            message=tester.translate("c15a15_final", "WatchYellowLed"),
            caption=tester.translate("c15a15_final", "capOutputLed"),
        )
        self["oYesNoYellowOn"] = sensor.YesNo(
            message=tester.translate("c15a15_final", "IsYellowLedOn?"),
            caption=tester.translate("c15a15_final", "capOutputLed"),
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
                ("dmm_Voutfl", "Voutfl", "oVout", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoYellowOff", "Notify", "oYesNoYellowOff", ""),
                ("ui_NotifyYellow", "Notify", "oNotifyYellow", ""),
                ("ui_YesNoYellowOn", "Notify", "oYesNoYellowOn", ""),
                ("ramp_OCP", "OCP", "oOCP", ""),
            )
        )
