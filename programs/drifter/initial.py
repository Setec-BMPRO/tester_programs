#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""Drifter(BM) Initial Test Program."""

import pathlib
import time

import libtester
import serial
import tester

import share
from . import console


class Initial(share.TestSequence):
    """Drifter Initial Test Program."""

    # Calibration values
    force_offset = -8
    force_threshold = 160
    # Limits common to both versions
    _common = (
        libtester.LimitDelta("Vin", 12.0, 0.1),
        libtester.LimitDelta("Vsw", 0, 100),
        libtester.LimitDelta("Vref", 0, 100),
        libtester.LimitDelta("Vcc", 3.30, 0.07),
        libtester.LimitDelta("Isense", -90, 5),
        libtester.LimitBetween("3V3", -3.3, -2.5),
        libtester.LimitDelta("%ErrorV", 0, 2.24),
        libtester.LimitDelta("%CalV", 0, 0.36),
        libtester.LimitDelta("%ErrorI", 0, 2.15),
        libtester.LimitDelta("%CalI", 0, 0.50),
        # Data reported by the PIC
        libtester.LimitInteger("PicStatus 0", 0),
        libtester.LimitDelta("PicZeroChk", 0, 65.0),
        libtester.LimitDelta("PicVin", 12.0, 0.5),
        libtester.LimitDelta("PicIsense", -90, 5),
        libtester.LimitDelta("PicVfactor", 20000, 1000),
        libtester.LimitDelta("PicIfactor", 15000, 1000),
        libtester.LimitBetween("PicIoffset", -8.01, -8),
        libtester.LimitBetween("PicIthreshold", 160, 160.01),
    )
    # Test limit selection keyed by program parameter
    limitdata = {
        "STD": {
            "Limits": _common + (libtester.LimitBetween("0V8", -1.2, -0.4),),
            "Software": "Drifter-5.hex",
        },
        "BM": {
            "Limits": _common + (libtester.LimitBetween("0V8", -1.4, -0.6),),
            "Software": "DrifterBM-2.hex",
        },
    }

    def open(self):
        """Prepare for testing."""
        Devices.fixture = self.fixture
        super().configure(
            self.limitdata[self.parameter]["Limits"], Devices, Sensors, Measurements
        )
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("CalPre", self._step_cal_pre),
            tester.TestStep("Calibrate", self._step_calibrate),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input DC and measure voltages."""
        dev["dcs_Vin"].output(12.0, output=True, delay=2)
        self.measure(("dmm_vin", "dmm_Vcc"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""
        mes["ProgramPIC"]()

    @share.teststep
    def _step_cal_pre(self, dev, mes):
        """Calibrate the PIC."""
        # Wait for console to be ready after programming.
        time.sleep(4)
        pic = dev["pic"]
        pic.open()
        pic["UNLOCK"] = True
        pic["NVDEFAULT"] = True
        pic["RESTART"] = True
        time.sleep(4)
        pic["UNLOCK"] = True
        mes["pic_Status"](timeout=5)
        pic["APS_DISABLE"] = 1
        self.measure(
            (
                "dmm_Vsw",
                "dmm_Vref",
                "dmm_3V3",
                "dmm_0V8",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate zero current, voltage, high current."""
        # Simulate zero current
        with dev["rla_ZeroCal"]:
            time.sleep(0.2)
            pic = dev["pic"]
            self._cal_reload(pic)
            mes["pic_ZeroChk"](timeout=5)
            # Auto-zero the PIC current
            pic["CAL_I_ZERO"] = True
            # Assign forced offset & threshold for current display
            pic["CAL_OFFSET_CURRENT"] = self.force_offset
            pic["ZERO-CURRENT-DISPLAY-THRESHOLD"] = self.force_threshold
            # Calibrate voltage
            dmm_vin = mes["dmm_vin"](timeout=5).value1
            pic_vin = mes["pic_vin"](timeout=5).value1
            err = ((dmm_vin - pic_vin) / dmm_vin) * 100
            mes["ErrorV"].sensor.store(err)
            mes["ErrorV"]()
            adjust_vcal = err != self.limits["%CalV"]
            # Adjust voltage if required
            if adjust_vcal:
                pic["CAL_V_SLOPE"] = dmm_vin
        # Simulate a high current
        dev["dcs_SlopeCal"].output(17.1, output=True, delay=0.2)
        self._cal_reload(pic)
        if adjust_vcal:
            # This will check any voltage adjust done above
            # ...we are using this CAL_RELOAD to save 10sec
            pic_vin = mes["pic_vin"](timeout=5).value1
            err = ((dmm_vin - pic_vin) / dmm_vin) * 100
            mes["CalV"].sensor.store(err)
            mes["CalV"]()
        # Now we proceed to calibrate the current
        dmm_isense = mes["dmm_isense"](timeout=5).value1
        pic_isense = mes["pic_isense"](timeout=5).value1
        err = ((dmm_isense - pic_isense) / dmm_isense) * 100
        mes["ErrorI"].sensor.store(err)
        mes["ErrorI"]()
        # Adjust current if required
        if err != self.limits["%CalI"]:
            pic["CAL_I_SLOPE"] = dmm_isense
            self._cal_reload(pic)
            pic_isense = mes["pic_isense"](timeout=5).value1
            err = ((dmm_isense - pic_isense) / dmm_isense) * 100
            mes["CalI"].sensor.store(err)
            mes["CalI"]()
        dev["dcs_SlopeCal"].output(0.0, output=False)
        # Write all adjusted parameters in a single write
        pic["NVWRITE"] = True
        time.sleep(5)
        # Read internal settings
        self.measure(
            (
                "pic_Vfactor",
                "pic_Ifactor",
                "pic_Ioffset",
                "pic_Ithreshold",
            ),
            timeout=5,
        )

    @staticmethod
    def _cal_reload(pic):
        """Re-Load data readings.

        @param pic PIC logical device.

        """
        pic["CAL_RELOAD"] = True
        time.sleep(10)


class Devices(share.Devices):
    """Devices."""

    fixture = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_SlopeCal", tester.DCSource, "DCS2"),
            ("dcs_Vin", tester.DCSource, "DCS3"),
            ("rla_Prog", tester.Relay, "RLA1"),
            ("rla_ZeroCal", tester.Relay, "RLA2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_Prog"])
        )
        # Serial connection to the console
        pic_ser = serial.Serial(baudrate=9600, timeout=5)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = share.config.Fixture.port(self.fixture, "PIC")
        self["pic"] = console.Console(pic_ser)

    def reset(self):
        """Reset instruments."""
        self["pic"].close()
        for dcs in ("dcs_SlopeCal", "dcs_Vin"):
            self[dcs].output(0.0, output=False)
        for rla in ("rla_Prog", "rla_ZeroCal"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        pic = self.devices["pic"]
        sensor = tester.sensor
        self["oMirErrorV"] = sensor.Mirror()
        self["oMirErrorI"] = sensor.Mirror()
        self["oVin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self["oVsw"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self["oVref"] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.001)
        self["oVcc"] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self["oIsense"] = sensor.Vdc(
            dmm, high=5, low=1, rng=10, res=0.00001, scale=-1000.0
        )
        self["o3V3"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self["o0V8"] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        sw_file = Initial.limitdata[self.parameter]["Software"]
        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"], pathlib.Path(__file__).parent / sw_file, "18F87J93"
        )
        for sen, cmd in (
            ("pic_Status", "NVSTATUS"),
            ("pic_ZeroChk", "ZERO_CURRENT"),
            ("pic_Vin", "VOLTAGE"),
            ("pic_isense", "CURRENT"),
            ("pic_Vfactor", "V_FACTOR"),
            ("pic_Ifactor", "I_FACTOR"),
            ("pic_Ioffset", "CAL_OFFSET_CURRENT"),
            ("pic_Ithreshold", "ZERO-CURRENT-DISPLAY-THRESHOLD"),
        ):
            self[sen] = sensor.Keyed(pic, cmd)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ErrorV", "%ErrorV", "oMirErrorV", ""),
                ("CalV", "%CalV", "oMirErrorV", ""),
                ("ErrorI", "%ErrorI", "oMirErrorI", ""),
                ("CalI", "%CalI", "oMirErrorI", ""),
                ("dmm_vin", "Vin", "oVin", ""),
                ("dmm_Vsw", "Vsw", "oVsw", ""),
                ("dmm_Vref", "Vref", "oVref", ""),
                ("dmm_Vcc", "Vcc", "oVcc", ""),
                ("dmm_isense", "Isense", "oIsense", ""),
                ("dmm_3V3", "3V3", "o3V3", ""),
                ("dmm_0V8", "0V8", "o0V8", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
                ("pic_Status", "PicStatus 0", "pic_Status", ""),
                ("pic_ZeroChk", "PicZeroChk", "pic_ZeroChk", ""),
                ("pic_vin", "PicVin", "pic_Vin", ""),
                ("pic_isense", "PicIsense", "pic_isense", ""),
                ("pic_Vfactor", "PicVfactor", "pic_Vfactor", ""),
                ("pic_Ifactor", "PicIfactor", "pic_Ifactor", ""),
                ("pic_Ioffset", "PicIoffset", "pic_Ioffset", ""),
                ("pic_Ithreshold", "PicIthreshold", "pic_Ithreshold", ""),
            )
        )
