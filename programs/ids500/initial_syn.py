#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 SynBuck Initial Test Program."""

import pathlib

import libtester
import tester

import share
from . import config


class InitialSyn(share.TestSequence):
    """IDS-500 Initial SynBuck Test Program."""

    # Test limits
    limitdata = (
        libtester.LimitDeltaLoHi("20VT", 20.0, 1.5, 2.0),
        libtester.LimitDelta("-20V", -20.0, 2.0),
        libtester.LimitDeltaLoHi("9V", 9.0, 1.0, 2.5),
        libtester.LimitDelta("TecOff", 0, 0.5),
        libtester.LimitLow("Tec0V", 1.0),
        libtester.LimitDelta("Tec2V5", 7.5, 0.3),
        libtester.LimitDelta("Tec5V", 15.0, 0.5),
        libtester.LimitDelta("Tec5V_Rev", -15.0, 0.5),
        libtester.LimitLow("TecVmonOff", 0.5),
        libtester.LimitLow("TecVmon0V", 0.8),
        libtester.LimitPercent("TecVmon2V5", 2.5, 2.5),
        libtester.LimitPercent("TecVmon5V", 5.0, 1.5),
        libtester.LimitLow("TecVsetOff", 0.5),
        libtester.LimitLow("LddOff", 0.5),
        libtester.LimitLow("Ldd0A", 0.5),
        libtester.LimitBetween("Ldd6A", 0.6, 1.8, doc="Vout @ 6A"),
        libtester.LimitBetween("Ldd50A", 1.0, 2.5, doc="Vout @ 50A"),
        libtester.LimitLow("LddVmonOff", 0.5),
        libtester.LimitLow("LddImonOff", 0.5),
        libtester.LimitLow("LddImon0V", 0.05),
        libtester.LimitDelta("LddImon0V6", 0.60, 0.05),
        libtester.LimitDelta("LddImon5V", 5.0, 0.2),
        libtester.LimitLow("ISIout0A", 1.0),
        libtester.LimitDelta("ISIout6A", 6.0, 1.0),
        libtester.LimitDelta("ISIout50A", 50.0, 2.0),
        libtester.LimitDelta("ISIset5V", 5.0, 0.2),
        libtester.LimitPercent("AdjLimits", 50.0, 0.2),
        libtester.LimitLow("FixtureLock", 20),
    )

    def open(self):
        """Prepare for testing."""
        Sensors.pic_hex_syn = config.pic_hex_syn
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Program", self._step_program),
            tester.TestStep("PowerUp", self._step_pwrup),
            tester.TestStep("TecEnable", self._step_tec_enable),
            tester.TestStep("TecReverse", self._step_tec_rev),
            tester.TestStep("LddEnable", self._step_ldd_enable),
            tester.TestStep("ISSetAdj", self._step_ISset_adj),
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Check Fixture Lock, apply Vcc and program the board."""
        mes["dmm_lock"](timeout=5)
        dev["dcs_vsec5Vlddtec"].output(5.0, True)
        mes["ProgramPIC"]()

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power up internal IDS-500 for 20VT,-20V, 9V rails and measure."""
        dev["dcs_fan"].output(12.0, output=True)
        dev["acsource"].output(voltage=240.0, output=True, delay=1.0)
        self.measure(
            (
                "dmm_20VT",
                "dmm__20V",
                "dmm_9V",
                "dmm_tecOff",
                "dmm_lddOff",
                "dmm_lddVmonOff",
                "dmm_lddImonOff",
                "dmm_tecVmonOff",
                "dmm_tecVsetOff",
            ),
            timeout=2,
        )

    @share.teststep
    def _step_tec_enable(self, dev, mes):
        """Enable TEC, set dc input and measure voltages."""
        dev["rla_tecphase"].set_on(delay=0.5)
        dev["rla_enable"].set_on(delay=0.5)
        dev["rla_enTec"].set_on(delay=0.5)
        dev["dcs_tecvset"].output(0.0, output=True)
        self.measure(
            (
                "dmm_tecVmon0V",
                "dmm_tec0V",
            ),
            timeout=2,
        )
        dev["dcs_tecvset"].output(2.5)
        self.measure(
            (
                "dmm_tecVmon2V5",
                "dmm_tec2V5",
            ),
            timeout=2,
        )
        dev["dcs_tecvset"].output(5.0)
        self.measure(
            (
                "dmm_tecVmon5V",
                "dmm_tec5V",
            ),
            timeout=2,
        )

    @share.teststep
    def _step_tec_rev(self, dev, mes):
        """Reverse TEC and measure voltages."""
        dev["rla_tecphase"].set_off()
        self.measure(
            (
                "dmm_tecVmon5V",
                "dmm_tec5Vrev",
            ),
            timeout=2,
        )
        dev["rla_tecphase"].set_on()
        self.measure(
            (
                "dmm_tecVmon5V",
                "dmm_tec5V",
            ),
            timeout=2,
        )

    @share.teststep
    def _step_ldd_enable(self, dev, mes):
        """Enable LDD, set dc input and measure voltages."""
        self.relay(
            (
                ("rla_interlock", True),
                ("rla_enIs", True),
                ("rla_lddcrowbar", True),
                ("rla_lddtest", True),
            )
        )
        dev["dcs_lddiset"].output(0.0, output=True)
        self.measure(
            (
                "dmm_ldd0V",
                "dmm_ISIout0A",
                "dmm_lddImon0V",
            ),
            timeout=2,
        )
        dev["dcs_lddiset"].output(0.6)
        self.measure(
            (
                "dmm_ldd0V6",
                "dmm_ISIout6A",
                "dmm_lddImon0V6",
            ),
            timeout=2,
        )
        dev["dcs_lddiset"].output(5.0)
        self.measure(
            (
                "dmm_ldd5V",
                "dmm_ISIout50A",
                "dmm_lddImon5V",
            ),
            timeout=2,
        )
        dev["dcs_lddiset"].output(0.0)

    @share.teststep
    def _step_ISset_adj(self, dev, mes):
        """ISset adjustment.

        Set LDD current to 50A.
        Calculate adjustment limits from measured current setting.
        Adjust pot R489 for accuracy of LDD output current.
        Measure LDD output current with calculated limits.

        """
        dev["dcs_lddiset"].output(5.0, True, delay=0.5)
        setI = mes["dmm_ISIset5V"](timeout=5).value1 * 10  # 5V == 50A
        self.limits["AdjLimits"].adjust(nominal=setI)
        lo_lim, hi_lim = self.limits["AdjLimits"].limit
        mes["ui_AdjLdd"].sensor.low = lo_lim
        mes["ui_AdjLdd"].sensor.high = hi_lim
        self.measure(
            (
                "ui_AdjLdd",
                "dmm_ISIoutPost",
                "dmm_lddImon5V",
            ),
            timeout=2,
        )


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_vsec5Vlddtec", tester.DCSource, "DCS1"),
            ("dcs_lddiset", tester.DCSource, "DCS2"),
            ("dcs_tecvset", tester.DCSource, "DCS3"),
            ("dcs_fan", tester.DCSource, "DCS5"),
            ("rla_enTec", tester.Relay, "RLA1"),
            ("rla_enIs", tester.Relay, "RLA2"),
            ("rla_lddcrowbar", tester.Relay, "RLA3"),
            ("rla_interlock", tester.Relay, "RLA4"),
            ("rla_lddtest", tester.Relay, "RLA5"),
            ("rla_tecphase", tester.Relay, "RLA6"),
            ("rla_enable", tester.Relay, "RLA12"),
            ("rla_syn", tester.Relay, "RLA7"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_syn"])
        )

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset(delay=2)
        self["discharge"].pulse()
        for dcs in (
            "dcs_vsec5Vlddtec",
            "dcs_lddiset",
            "dcs_tecvset",
            "dcs_fan",
        ):
            self[dcs].output(0.0, False)
        for rla in (
            "rla_enTec",
            "rla_enIs",
            "rla_lddcrowbar",
            "rla_interlock",
            "rla_lddtest",
            "rla_tecphase",
            "rla_enable",
            "rla_syn",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    # Firmware image
    pic_hex_syn = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["IS_Vmon"] = sensor.Vdc(dmm, high=5, low=6, rng=10, res=0.001)
        self["IS_Iout"] = sensor.Vdc(dmm, high=6, low=6, rng=10, res=0.001)
        self["IS_Iset"] = sensor.Vdc(dmm, high=7, low=6, rng=10, res=0.001)
        self["LDDshunt"] = sensor.Vdc(
            dmm, high=8, low=4, rng=0.1, res=0.0001, scale=1000, nplc=10
        )
        self["20VT"] = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self["9V"] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.001)
        self["Minus20V"] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self["Lock"] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self["TEC_Vset"] = sensor.Vdc(dmm, high=14, low=1, rng=10, res=0.001)
        self["TECoutput"] = sensor.Vdc(dmm, high=15, low=3, rng=100, res=0.001)
        self["TEC_Vmon"] = sensor.Vdc(dmm, high=24, low=1, rng=10, res=0.001)
        self["LDDoutput"] = sensor.Vdc(dmm, high=21, low=1, rng=10, res=0.001)
        lo_lim, hi_lim = self.limits["AdjLimits"].limit
        self["oAdjLdd"] = sensor.AdjustAnalog(
            sensor=self["LDDshunt"],
            low=lo_lim,
            high=hi_lim,
            message=tester.translate("IDS500 Initial Syn", "AdjR489"),
            caption=tester.translate("IDS500 Initial Syn", "capAdjLdd"),
        )
        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / self.pic_hex_syn,
            "18F4321",
        )


class Measurements(share.Measurements):
    """SynBuck Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "Lock", ""),
                ("dmm_20VT", "20VT", "20VT", ""),
                ("dmm__20V", "-20V", "Minus20V", ""),
                ("dmm_9V", "9V", "9V", ""),
                ("dmm_tecOff", "TecOff", "TECoutput", ""),
                ("dmm_tec0V", "Tec0V", "TECoutput", ""),
                ("dmm_tec2V5", "Tec2V5", "TECoutput", ""),
                ("dmm_tec5V", "Tec5V", "TECoutput", ""),
                ("dmm_tec5Vrev", "Tec5V_Rev", "TECoutput", ""),
                ("dmm_tecVmonOff", "TecVmonOff", "TEC_Vmon", ""),
                ("dmm_tecVmon0V", "TecVmon0V", "TEC_Vmon", ""),
                ("dmm_tecVmon2V5", "TecVmon2V5", "TEC_Vmon", ""),
                ("dmm_tecVmon5V", "TecVmon5V", "TEC_Vmon", ""),
                ("dmm_tecVsetOff", "TecVsetOff", "TEC_Vset", ""),
                ("dmm_lddOff", "LddOff", "LDDoutput", ""),
                ("dmm_ldd0V", "Ldd0A", "LDDoutput", ""),
                ("dmm_ldd0V6", "Ldd6A", "LDDoutput", ""),
                ("dmm_ldd5V", "Ldd50A", "LDDoutput", ""),
                ("dmm_lddVmonOff", "LddVmonOff", "IS_Vmon", ""),
                ("dmm_lddImonOff", "LddImonOff", "IS_Iout", ""),
                ("dmm_lddImon0V", "LddImon0V", "IS_Iout", ""),
                ("dmm_lddImon0V6", "LddImon0V6", "IS_Iout", ""),
                ("dmm_lddImon5V", "LddImon5V", "IS_Iout", ""),
                ("dmm_ISIout0A", "ISIout0A", "LDDshunt", ""),
                ("dmm_ISIout6A", "ISIout6A", "LDDshunt", ""),
                ("dmm_ISIout50A", "ISIout50A", "LDDshunt", ""),
                ("dmm_ISIset5V", "ISIset5V", "IS_Iset", ""),
                ("ui_AdjLdd", "Notify", "oAdjLdd", ""),
                ("dmm_ISIoutPost", "AdjLimits", "LDDshunt", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
            )
        )
