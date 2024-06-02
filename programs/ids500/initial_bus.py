#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 Bus Initial Test Program."""

import tester

import share


class InitialBus(share.TestSequence):
    """IDS-500 Initial Bus Test Program."""

    # Test limits
    limitdata = (
        tester.LimitBetween("400V", 390, 410),
        tester.LimitBetween("20VT_load0_out", 22.0, 24.0),
        tester.LimitBetween("9V_load0_out", 10.8, 12.0),
        tester.LimitBetween("20VL_load0_out", 22.0, 24.0),
        tester.LimitBetween("-20V_load0_out", -25.0, -22.0),
        tester.LimitBetween("20VT_load1_out", 22.0, 25.0),
        tester.LimitBetween("9V_load1_out", 9.0, 11.0),
        tester.LimitBetween("20VL_load1_out", 22.0, 25.0),
        tester.LimitBetween("-20V_load1_out", -26.0, -22.0),
        tester.LimitBetween("20VT_load2_out", 19.0, 24.0),
        tester.LimitBetween("9V_load2_out", 9.0, 11.0),
        tester.LimitBetween("20VL_load2_out", 19.0, 21.5),
        tester.LimitBetween("-20V_load2_out", -22.2, -20.0),
        tester.LimitBetween("20VT_load3_out", 17.5, 20.0),
        tester.LimitBetween("9V_load3_out", 9.0, 12.0),
        tester.LimitBetween("20VL_load3_out", 22.0, 24.0),
        tester.LimitBetween("-20V_load3_out", -26.0, -22.0),
        tester.LimitLow("FixtureLock", 20),
    )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_pwrup),
            tester.TestStep("TecLddStartup", self._step_tec_ldd),
        )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
        mes["dmm_lock"](timeout=5)
        self.dcsource(
            (
                ("dcs_prictl", 13.0),
                ("dcs_fan", 12.0),
            )
        )
        dev["acsource"].output(voltage=240.0, output=True, delay=0.5)
        mes["dmm_400V"](timeout=5)

    @share.teststep
    def _step_tec_ldd(self, dev, mes):
        """ """
        self.relay(
            (
                ("rla_enBC20", True),
                ("rla_enT", True),
                ("rla_enBC9", True),
                ("rla_enL", True),
            )
        )
        self.dcload(
            (
                ("dcl_20VT", 0.0),
                ("dcl_9V", 0.0),
                ("dcl_20VL", 0.0),
                ("dcl__20", 0.0),
            )
        )
        self.measure(
            (
                "dmm_20VT_0",
                "dmm_9V_0",
                "dmm_20VL_0",
                "dmm__20V_0",
            ),
            timeout=5,
        )
        dev["dcl_9V"].output(10.0)
        self.measure(
            (
                "dmm_20VT_1",
                "dmm_9V_1",
                "dmm_20VL_1",
                "dmm__20V_1",
            ),
            timeout=5,
        )
        self.dcload(
            (
                ("dcl_20VL", 2.0),
                ("dcl__20", 0.4),
            )
        )
        self.measure(
            (
                "dmm_20VT_2",
                "dmm_9V_2",
                "dmm_20VL_2",
                "dmm__20V_2",
            ),
            timeout=5,
        )
        self.dcload(
            (
                ("dcl_20VT", 15.0),
                ("dcl_9V", 0.0),
                ("dcl_20VL", 0.0),
                ("dcl__20", 0.0),
            )
        )
        self.measure(
            (
                "dmm_20VT_3",
                "dmm_9V_3",
                "dmm_20VL_3",
                "dmm__20V_3",
            ),
            timeout=5,
        )


class Devices(share.Devices):
    """Bus Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_prictl", tester.DCSource, "DCS4"),
            ("dcs_fan", tester.DCSource, "DCS5"),
            ("dcl_20VT", tester.DCLoad, "DCL1"),
            ("dcl_9V", tester.DCLoad, "DCL2"),
            ("dcl_20VL", tester.DCLoad, "DCL3"),
            ("dcl__20", tester.DCLoad, "DCL4"),
            ("rla_enT", tester.Relay, "RLA1"),
            ("rla_enBC9", tester.Relay, "RLA2"),
            ("rla_enL", tester.Relay, "RLA3"),
            ("rla_enBC20", tester.Relay, "RLA4"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset(delay=2)
        self["discharge"].pulse()
        for dcs in (
            "dcs_prictl",
            "dcs_fan",
        ):
            self[dcs].output(0.0, False)
        for dcl in (
            "dcl_20VT",
            "dcl_9V",
            "dcl_20VL",
            "dcl__20",
        ):
            self[dcl].output(0.0, False)
        for rla in (
            "rla_enT",
            "rla_enBC9",
            "rla_enL",
            "rla_enBC20",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Bus Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["olock"] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self["o400V"] = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self["o20VT"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self["o9V"] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self["o20VL"] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.001)
        self["o_20V"] = sensor.Vdc(dmm, high=20, low=1, rng=100, res=0.001)


class Measurements(share.Measurements):
    """Bus Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "olock", ""),
                ("dmm_400V", "400V", "o400V", ""),
                ("dmm_20VT_0", "20VT_load0_out", "o20VT", ""),
                ("dmm_9V_0", "9V_load0_out", "o9V", ""),
                ("dmm_20VL_0", "20VL_load0_out", "o20VL", ""),
                ("dmm__20V_0", "-20V_load0_out", "o_20V", ""),
                ("dmm_20VT_1", "20VT_load1_out", "o20VT", ""),
                ("dmm_9V_1", "9V_load1_out", "o9V", ""),
                ("dmm_20VL_1", "20VL_load1_out", "o20VL", ""),
                ("dmm__20V_1", "-20V_load1_out", "o_20V", ""),
                ("dmm_20VT_2", "20VT_load2_out", "o20VT", ""),
                ("dmm_9V_2", "9V_load2_out", "o9V", ""),
                ("dmm_20VL_2", "20VL_load2_out", "o20VL", ""),
                ("dmm__20V_2", "-20V_load2_out", "o_20V", ""),
                ("dmm_20VT_3", "20VT_load3_out", "o20VT", ""),
                ("dmm_9V_3", "9V_load3_out", "o9V", ""),
                ("dmm_20VL_3", "20VL_load3_out", "o20VL", ""),
                ("dmm__20V_3", "-20V_load3_out", "o_20V", ""),
            )
        )
