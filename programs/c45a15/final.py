#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""C45A-15 Final Test Program."""

import tester

import share


class Final(share.TestSequence):

    """C45A-15 Final Test Program."""

    limitdata = (
        tester.LimitBetween("Vstart", 8.55, 9.45),
        tester.LimitBetween("Vout", 15.6, 16.4),
        tester.LimitLow("Vshdn", 8.0),
        tester.LimitLow("Voff", 1.0),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("ConnectCMR", self._step_connect_cmr),
            tester.TestStep("Load", self._step_load),
            tester.TestStep("Restart", self._step_restart),
            tester.TestStep("Poweroff", self._step_power_off),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Switch on unit at 240Vac, measure output, check Green led."""
        dev["acsource"].output(240.0, output=True, delay=0.5)
        self.measure(("dmm_Vstart", "ui_YesNoGreen"), timeout=5)

    @share.teststep
    def _step_connect_cmr(self, dev, mes):
        """
        Connect the CMR-SBP Bus, measure output, check Yellow and Red leds.
        """
        dev["rla_Bus"].set_on()
        self.measure(("ui_YesNoYellow", "dmm_Vout", "ui_YesNoRed"), timeout=8)

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure output at startup load, full load, and shutdown load."""
        dev["dcl"].output(0.3, output=True)
        mes["dmm_Vout"](timeout=5)
        dev["dcl"].output(2.8, delay=2)
        mes["dmm_Vout"](timeout=5)
        dev["dcl"].output(3.5)
        mes["dmm_Vshdn"](timeout=5)

    @share.teststep
    def _step_restart(self, dev, mes):
        """Restart the unit, measure output."""
        dev["rla_Bus"].set_off()
        dev["acsource"].output(0.0)
        dev["dcl"].output(2.8, delay=1)
        dev["dcl"].output(0.0, output=False, delay=1)
        dev["acsource"].output(240.0, delay=0.5)
        mes["dmm_Vstart"](timeout=5)

    @share.teststep
    def _step_power_off(self, dev, mes):
        """Switch off unit, measure output."""
        dev["dcl"].output(2.8, output=True)
        dev["acsource"].output(0.0)
        self.measure(("dmm_Voff", "ui_NotifyOff"), timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcl", tester.DCLoad, "DCL1"),
            ("rla_Bus", tester.Relay, "RLA1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(0.0, False)
        self["rla_Bus"].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oVout"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self["oYesNoGreen"] = sensor.YesNo(
            message=tester.translate("c45a15_final", "IsPowerLedGreen?"),
            caption=tester.translate("c45a15_final", "capPowerLed"),
        )
        self["oYesNoYellow"] = sensor.YesNo(
            message=tester.translate("c45a15_final", "WaitYellowLedOn?"),
            caption=tester.translate("c45a15_final", "capOutputLed"),
        )
        self["oYesNoRed"] = sensor.YesNo(
            message=tester.translate("c45a15_final", "WaitRedLedFlash?"),
            caption=tester.translate("c45a15_final", "capOutputLed"),
        )
        self["oNotifyOff"] = sensor.Notify(
            message=tester.translate("c45a15_final", "WaitAllLedsOff"),
            caption=tester.translate("c45a15_final", "capAllOff"),
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_Vstart", "Vstart", "oVout", ""),
                ("dmm_Vout", "Vout", "oVout", ""),
                ("dmm_Vshdn", "Vshdn", "oVout", ""),
                ("dmm_Voff", "Voff", "oVout", ""),
                ("ui_YesNoGreen", "Notify", "oYesNoGreen", ""),
                ("ui_YesNoYellow", "Notify", "oYesNoYellow", ""),
                ("ui_YesNoRed", "Notify", "oYesNoRed", ""),
                ("ui_NotifyOff", "Notify", "oNotifyOff", ""),
            )
        )
