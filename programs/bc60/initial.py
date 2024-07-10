#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd
"""BC60 Initial Test Program."""

import libtester
import serial
import tester

import share
from . import console


class Initial(share.TestSequence):
    """Initial Test Program."""

    limits = (
        libtester.LimitLow("FixtureLock", 200),
        libtester.LimitDelta("Vac", 240.0, 5.0),
        libtester.LimitBetween("Vbus", 330.0, 350.0),
        libtester.LimitPercent("VccPri", 15.6, 5.0),
        libtester.LimitPercent("VccBias", 15.0, 13.0),
        libtester.LimitLow("VbatOff", 0.5),
        libtester.LimitBetween("AlarmClosed", 1000, 3000),
        libtester.LimitBetween("AlarmOpen", 11000, 13000),
        libtester.LimitBetween("Status 0", -0.1, 0.1),
        libtester.LimitBetween("OutOCP", 20.05, 24.00),
        libtester.LimitBetween("BattOCP", 14.175, 15.825),
        libtester.LimitLow("InOCP", 13.0),
        libtester.LimitPercent("VoutPreCal", 13.8, 2.6),
#        libtester.LimitDelta("VoutPostCal", 13.8, _cal_factor * 0.15),
        libtester.LimitBetween("MspVout", 13.0, 14.6),
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Calibration", self._step_cal),
            tester.TestStep("OCP", self._step_ocp),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare: Dc input, measure."""
        dev["dcs_sec"].output(self._vcc_bias_set, output=True)
        self.measure(
            (
                "dmm_lock",
                "dmm_vccbiasext",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up the unit at 240Vac and measure voltages at min load."""
        dev["acsource"].output(voltage=240.0, output=True, delay=1.0)
        dev["dcl_vbat"].output(0.1, output=True)
        self.measure(
            (
                "dmm_vac",
                "dmm_vbus",
                "dmm_vccpri",
                "dmm_vccbias",
                "dmm_vbatoff",
                "dmm_alarmclose",
            ),
            timeout=5,
        )
        dev["dcl_vbat"].output(0.0)

    @share.teststep
    def _step_cal(self, dev, mes):
        """Calibration."""
        with dev["msp"] as msp:
            msp.initialise()
            mes["msp_status"]()
            msp.filter_reload()
            mes["msp_vout"]()
            dmm_V = mes["dmm_voutpre"].stable(delta=0.005).value1
            msp["CAL-V"] = dmm_V
            mes["dmm_voutpost"].stable(delta=0.005)
            msp["NV-WRITE"] = True
            mes["msp_status"]()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        self.measure(("dmm_alarmopen", "ramp_battocp"), timeout=5)
        dev["dcl_vbat"].output(0.0)
        mes["ramp_outocp"](timeout=5)
        dev["dcl_vout"].output(0.0)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_sec", tester.DCSource, "DCS1"),
            ("rla_prog", tester.Relay, "RLA1"),  # Off: STM, On: Laird BLE
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcl_Vout"] = tester.DCLoadParallel(
            (
                (tester.DCLoad(self.physical_devices["DCL1"]), 10),
                (tester.DCLoad(self.physical_devices["DCL3"]), 10),
            )
        )
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = self.port("STM")
        self["con"] = console.Console(con_ser)

    def reset(self):
        """Reset instruments."""
        self["con"].close()
        self["acsource"].reset()
        self["dcl_vout"].output(10.0, delay=1.0)
        self["discharge"].pulse()
        self["dcl_vout"].output(0.0, output=False)
        self["dcs_sec"].output(0.0, output=False)
        self["rla_prog"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        msp = self.devices["msp"]
        sensor = tester.sensor
        self["lock"] = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self["Vac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self["Vac"].doc = "240Vac input"
        self["Vpfc"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self["Vpfc"].doc = "PFC bus"
        self["12Vpri"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self["12Vpri"].doc = "12VPri bus"
        self["12Vpri_rla"] = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.01)
        self["12Vpri_rla"].doc = "Power to K1"
        self["15Vsb"] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self["15Vsb"].doc = "15Vsb rail"
        self["5V"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["5V"].doc = "5V rail"
        self["3V3"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.001)
        self["3V3"].doc = "3V3 rail"
        self["Vout"] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self["Vout"].doc = "Output"
        self["ACfan"] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.01)
        self["ACfan"].doc = "AC X201"
        self["DCfan"] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self["DCfan"].doc = "DC X202"
        self["Vcan"] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.01)
        self["Vcan"].doc = "CAN power"


        self["msp_stat"] = sensor.Keyed(msp, "MSP-STATUS")
        self["msp_stat"].doc = "MSP430 console"
        self["msp_vo"] = sensor.Keyed(msp, "MSP-VOUT")
        self["msp_vo"].doc = "MSP430 console"
        low, high = self.limits["OutOCP"].limit
        self["ocp_out"] = sensor.Ramp(
            stimulus=self.devices["dcl_vout"],
            sensor=self["vout"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=low - 0.5, stop=high + 0.5, step=0.05),
            delay=0.05,
        )
        low, high = self.limits["BattOCP"].limit
        self["ocp_batt"] = sensor.Ramp(
            stimulus=self.devices["dcl_vbat"],
            sensor=self["vbat"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=low - 0.5, stop=high + 0.5, step=0.05),
            delay=0.05,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", ""),
                ("dmm_vac", "Vac", "vac", ""),
                ("dmm_vbus", "Vbus", "vbus", ""),
                ("dmm_vccpri", "VccPri", "vcc_pri", ""),
                ("dmm_vccbiasext", "VccBiasExt", "vcc_bias", ""),
                ("dmm_vccbias", "VccBias", "vcc_bias", ""),
                ("dmm_voutpre", "VoutPreCal", "vout", "Output before Calibration"),
                ("dmm_voutpost", "VoutPostCal", "vout", "Output after Calibration"),
                ("ramp_outocp", "OutOCP", "ocp_out", ""),
            )
        )
