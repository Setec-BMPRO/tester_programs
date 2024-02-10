#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd.
"""Final Test Program for GENIUS-II and GENIUS-II-H."""

import tester

import share


class Final(share.TestSequence):

    """GENIUS-II Final Test Program."""

    # Common test limits
    _common = (
        tester.LimitBetween("InRes", 80e3, 170e3),
        tester.LimitHigh("DCinShort", 10),
        tester.LimitDelta("Vout", 13.675, 0.1),
        tester.LimitLow("VoutOff", 2.0),
        tester.LimitBetween("VoutStartup", 13.60, 14.10),
        tester.LimitDelta("Vbat", 13.675, 0.1),
        tester.LimitLow("VbatOff", 1.0),
        tester.LimitBetween("ExtBatt", 11.5, 12.8),
        tester.LimitLow("InOCP", 13.24),
        tester.LimitBetween("OCP", 34.0, 43.0),
    )
    # Test limit selection keyed by program parameter
    limitdata = {
        "STD": {
            "Limits": _common,
            "MaxBattLoad": 15.0,
            "LoadRatio": (29, 14),  # Vout:Vbat load ratio
        },
        "H": {
            "Limits": _common,
            "MaxBattLoad": 30.0,
            "LoadRatio": (3, 2),  # Vout:Vbat load ratio
        },
    }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]["Limits"], Devices, Sensors, Measurements
        )
        self.steps = (
            tester.TestStep("PartDetect", self._step_part_detect),
            tester.TestStep("PowerOn", self._step_poweron),
            tester.TestStep("BattFuse", self._step_battfuse),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("RemoteSw", self._step_remote_sw),
        )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Detect parts and check connections.

        Verify that the hand loaded input discharge resistors are there.
        Verify that the output wires are not swapped - DCin shorted to 0V.

        """
        self.measure(("dmm_inres", "dmm_dcinshort"), timeout=5)

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Switch on unit at 240Vac, no load."""
        dev["acsource"].output(240.0, output=True)
        self.measure(("dmm_vout", "dmm_vbat"), timeout=10)

    @share.teststep
    def _step_battfuse(self, dev, mes):
        """Remove and insert battery fuse, check red LED."""
        self.measure(
            ("ui_yesnofuseout", "dmm_vbatoff", "ui_yesnofusein", "dmm_vout"), timeout=5
        )

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Ramp up load until OCP, shutdown and recover."""
        dev["dcl"].output(0.0, output=True)
        dev["dcl"].binary(0.0, 32.0, 5.0)
        mes["ramp_ocp"]()
        dev["dcl"].output(47.0)
        mes["dmm_voutoff"](timeout=10)
        dev["dcl"].output(0.0)
        self.measure(
            (
                "dmm_voutstartup",
                "dmm_vout",
                "dmm_vbat",
            ),
            timeout=10,
        )

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Switch off AC, apply external Vbat, remote switch."""
        dev["acsource"].output(0.0)
        dev["dcl"].output(2.0, output=True, delay=1)
        dev["dcl"].output(0.1)
        dev["dcs_vbat"].output(12.6, output=True, delay=2)
        self.measure(
            (
                "dmm_vbatext",
                "dmm_voutext",
            ),
            timeout=5,
        )
        with dev["rla_remotesw"]:
            mes["dmm_voutoff"](timeout=10)
        mes["dmm_voutext"](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            # This DC Source simulates the battery voltage
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("dcl_vout", tester.DCLoad, "DCL1"),
            ("dcl_vbat", tester.DCLoad, "DCL3"),
            ("rla_remotesw", tester.Relay, "RLA1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        ratio_vout, ratio_vbat = Final.limitdata[self.parameter]["LoadRatio"]
        self["dcl"] = tester.DCLoadParallel(
            (
                (self["dcl_vout"], ratio_vout),
                (self["dcl_vbat"], ratio_vbat),
            )
        )

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl"].output(0.0)
        self["dcs_vbat"].output(0.0, False)
        self["rla_remotesw"].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["inres"] = sensor.Res(dmm, high=1, low=1, rng=1e6, res=1)
        self["dcinshrt"] = sensor.Res(dmm, high=5, low=3, rng=1e5, res=1)
        self["vout"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["vbat"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl"],
            sensor=self["vout"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=32.0, stop=48.0, step=0.2),
            delay=0.1,
        )
        self["yesnofuseout"] = sensor.YesNo(
            message=tester.translate(
                "geniusII_final", "RemoveBattFuseIsLedRedFlashing?"
            ),
            caption=tester.translate("geniusII_final", "capLedRed"),
        )
        self["yesnofusein"] = sensor.YesNo(
            message=tester.translate("geniusII_final", "ReplaceBattFuseIsLedGreen?"),
            caption=tester.translate("geniusII_final", "capLedRed"),
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_inres", "InRes", "inres", ""),
                ("dmm_dcinshort", "DCinShort", "dcinshrt", ""),
                ("dmm_vout", "Vout", "vout", ""),
                ("dmm_voutoff", "VoutOff", "vout", ""),
                ("dmm_voutstartup", "VoutStartup", "vout", ""),
                ("dmm_voutext", "ExtBatt", "vout", ""),
                ("dmm_vbat", "Vbat", "vbat", ""),
                ("dmm_vbatoff", "VbatOff", "vbat", ""),
                ("dmm_vbatext", "ExtBatt", "vbat", ""),
                ("ramp_ocp", "OCP", "ocp", ""),
                ("ui_yesnofuseout", "Notify", "yesnofuseout", ""),
                ("ui_yesnofusein", "Notify", "yesnofusein", ""),
            )
        )
