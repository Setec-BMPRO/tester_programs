#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""2040 Initial Test Program."""

import libtester
import tester

import share


class Initial(share.TestSequence):
    """2040 Initial Test Program."""

    limitdata = (
        libtester.LimitBetween("VccAC", 9.0, 16.5),
        libtester.LimitBetween("VccDC", 7.8, 14.0),
        libtester.LimitDelta("VbusMin", 130.0, 10.0),
        libtester.LimitDelta("SDOff", 20.0, 1.0),
        libtester.LimitLow("SDOn", 5.0),
        libtester.LimitDelta("ACmin", 90.0, 2.0),
        libtester.LimitDelta("ACtyp", 240.0, 2.0),
        libtester.LimitDelta("ACmax", 265.0, 2.0),
        libtester.LimitDelta("VoutExt", 20.0, 0.2),
        libtester.LimitDelta("Vout", 20.0, 0.4),
        libtester.LimitBetween("GreenOn", 15.0, 20.0),
        libtester.LimitBetween("RedDCOff", 9.0, 15.0),
        libtester.LimitBetween("RedDCOn", 1.8, 3.5),
        libtester.LimitBetween("RedACOff", 9.0, 50.0),
        libtester.LimitDelta("DCmin", 10.0, 1.0),
        libtester.LimitDelta("DCtyp", 24.5, 1.5),
        libtester.LimitDelta("DCmax", 40.0, 2.0),
        libtester.LimitBetween("OCP", 3.5, 4.1),
        libtester.LimitLow("inOCP", 19.0),
        libtester.LimitLow("FixtureLock", 20),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("FixtureLock", self._step_fixture_lock),
            tester.TestStep("SecCheck", self._step_sec_check),
            tester.TestStep("DCPowerOn", self._step_dcpower_on),
            tester.TestStep("ACPowerOn", self._step_acpower_on),
        )

    @share.teststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes["dmm_Lock"](timeout=5)

    @share.teststep
    def _step_sec_check(self, dev, mes):
        """Apply External DC voltage to output and measure voltages."""
        dev["dcs_Vout"].output(20.0, output=True)
        self.measure(
            (
                "dmm_VoutExt",
                "dmm_SDOff",
                "dmm_GreenOn",
            ),
            timeout=5,
        )
        dev["dcs_Vout"].output(0.0)

    @share.teststep
    def _step_dcpower_on(self, dev, mes):
        """Test with DC power in.

        Power with DC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        dev["dcs_dcin"].output(10.25, output=True)
        self.measure(
            ("dmm_DCmin", "dmm_VccDC", "dmm_Vout", "dmm_GreenOn", "dmm_RedDCOff"),
            timeout=5,
        )
        dev["dcl_Vout"].output(1.0, output=True, delay=1.0)
        mes["dmm_Vout"](timeout=5)
        dev["dcs_dcin"].output(40.0)
        self.measure(
            (
                "dmm_DCmax",
                "dmm_VccDC",
                "dmm_Vout",
            ),
            timeout=5,
        )
        dev["dcs_dcin"].output(25.0)
        self.measure(("dmm_DCtyp", "dmm_VccDC", "dmm_Vout", "ramp_OCP"), timeout=5)
        dev["dcl_Vout"].output(4.1, delay=0.5)
        self.measure(
            (
                "dmm_SDOn",
                "dmm_RedDCOn",
            ),
            timeout=5,
        )
        dev["dcl_Vout"].output(0.0)
        dev["dcs_dcin"].output(0.0, output=False, delay=2)

    @share.teststep
    def _step_acpower_on(self, dev, mes):
        """Test with AC power in.

        Power with AC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        dev["acsource"].output(voltage=90.0, output=True, delay=0.5)
        self.measure(
            (
                "dmm_ACmin",
                "dmm_VbusMin",
                "dmm_VccAC",
                "dmm_Vout",
                "dmm_GreenOn",
                "dmm_RedACOff",
            ),
            timeout=15,
        )
        dev["dcl_Vout"].output(2.0, delay=1.0)
        mes["dmm_Vout"](timeout=5)
        dev["acsource"].output(voltage=265.0, delay=0.5)
        self.measure(
            (
                "dmm_ACmax",
                "dmm_VccAC",
                "dmm_Vout",
            ),
            timeout=5,
        )
        dev["acsource"].output(voltage=240.0, delay=0.5)
        self.measure(("dmm_ACtyp", "dmm_VccAC", "dmm_Vout", "ramp_OCP"), timeout=5)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("dcs_Vout", tester.DCSource, "DCS1"),
            ("dcs_dcin1", tester.DCSource, "DCS2"),
            ("dcs_dcin2", tester.DCSource, "DCS3"),
            ("dcs_dcin3", tester.DCSource, "DCS4"),
            ("dcs_dcin4", tester.DCSource, "DCS5"),
            ("dcl_Vout", tester.DCLoad, "DCL4"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcs_dcin"] = tester.DCSourceParallel(
            (
                self["dcs_dcin1"],
                self["dcs_dcin2"],
                self["dcs_dcin3"],
                self["dcs_dcin4"],
            )
        )
        self["discharge"] = tester.Discharge(self.physical_devices["DIS"])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        for dcs in ("dcs_dcin", "dcs_Vout"):
            self[dcs].output(0.0, False)
        self["dcl_Vout"].output(1.0, delay=1)
        self["discharge"].pulse()
        self["dcl_Vout"].output(0.0, False)


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oLock"] = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self["oVccAC"] = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self["oVccDC"] = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self["oVbus"] = sensor.Vdc(dmm, high=3, low=5, rng=1000, res=0.01)
        self["oSD"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["oACin"] = sensor.Vac(dmm, high=5, low=4, rng=1000, res=0.01)
        self["oVout"] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self["oGreen"] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self["oRedDC"] = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self["oRedAC"] = sensor.Vdc(dmm, high=1, low=5, rng=100, res=0.001)
        self["oDCin"] = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self["oOCP"] = sensor.Ramp(
            stimulus=self.devices["dcl_Vout"],
            sensor=self["oVout"],
            detect_limit=self.limits["inOCP"],
            ramp_range=sensor.RampRange(start=3.2, stop=4.3, step=0.05),
            delay=0.15,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_Lock", "FixtureLock", "oLock", ""),
                ("dmm_VccAC", "VccAC", "oVccAC", ""),
                ("dmm_VccDC", "VccDC", "oVccDC", ""),
                ("dmm_VbusMin", "VbusMin", "oVbus", ""),
                ("dmm_SDOff", "SDOff", "oSD", ""),
                ("dmm_SDOn", "SDOn", "oSD", ""),
                ("dmm_ACmin", "ACmin", "oACin", ""),
                ("dmm_ACtyp", "ACtyp", "oACin", ""),
                ("dmm_ACmax", "ACmax", "oACin", ""),
                ("dmm_VoutExt", "VoutExt", "oVout", ""),
                ("dmm_Vout", "Vout", "oVout", ""),
                ("dmm_GreenOn", "GreenOn", "oGreen", ""),
                ("dmm_RedDCOff", "RedDCOff", "oRedDC", ""),
                ("dmm_RedDCOn", "RedDCOn", "oRedDC", ""),
                ("dmm_RedACOff", "RedACOff", "oRedAC", ""),
                ("dmm_DCmin", "DCmin", "oDCin", ""),
                ("dmm_DCtyp", "DCtyp", "oDCin", ""),
                ("dmm_DCmax", "DCmax", "oDCin", ""),
                ("ramp_OCP", "OCP", "oOCP", ""),
            )
        )
