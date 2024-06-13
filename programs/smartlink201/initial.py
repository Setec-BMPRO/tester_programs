#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import pathlib

import libtester
import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):
    """BLExtender/SmartLink201 Initial Test Program."""

    vin_set = 12.0  # Input voltage (V)
    limitdata = (
        libtester.LimitRegExp("BleMac", r"^[0-9a-f]{12}$", doc="Valid MAC address "),
        libtester.LimitLow("PartOk", 2.0, doc="All parts present"),
        libtester.LimitLow("S5tank", 2.0, doc="S5 tank ON"),
        libtester.LimitDelta("Vbatt", vin_set, 0.5, doc="At nominal"),
        libtester.LimitDelta("Vin", vin_set - 2.0, 0.5, doc="At nominal"),
        libtester.LimitPercent("3V3", 3.33, 3.0, doc="At nominal"),
        libtester.LimitDelta("SL_VbattPre", vin_set, 0.25, doc="Before cal"),
        libtester.LimitDelta("SL_Vbatt", vin_set, 0.05, doc="After cal"),
        # Analog tank inputs
        #   Open: approx. > 0xFF0
        #   Short:  Sense 1: 170-200    Sense 2-4: 60-80
        libtester.LimitHigh("TankHi", 0xF00),
        libtester.LimitLow("TankLo", 0x200),
    )
    analog_read_wait = 2  # Analog read response time
    sernum = None

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        Devices.sw_arm_image = self.cfg.sw_arm_image
        Sensors.sw_nrf_image = self.cfg.sw_nrf_image
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep(
                "PgmARM", self.devices["progARM"].program, self.cfg.is_smartlink
            ),
            tester.TestStep("PgmNordic", self._step_program_nordic),
            tester.TestStep("Nordic", self._step_test_nordic),
            tester.TestStep("Calibrate", self._step_calibrate, self.cfg.is_smartlink),
            tester.TestStep("TankSense", self._step_tank_sense, self.cfg.is_smartlink),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply Vbatt and check voltages."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_serialnum")
        # Product specific measurements
        meas1 = ("dmm_Parts2",)
        meas2 = (
            "dmm_Vbatt",
            "dmm_Vin",
            "dmm_3V3",
        )
        if self.cfg.is_smartlink:
            meas1 += ("dmm_Parts1",)
            meas2 += ("dmm_S5tank",)
        # Do the test
        self.measure(meas1, timeout=5)
        dev["dcs_Vbatt"].output(self.vin_set, output=True, delay=1)
        self.measure(meas2, timeout=5)

    @share.teststep
    def _step_program_nordic(self, dev, mes):
        """Program Nordic."""
        mes["JLink"]()

    @share.teststep
    def _step_test_nordic(self, dev, mes):
        """Test the Nordic device."""
        smartlink201 = dev["smartlink201"]
        smartlink201.open()
        smartlink201.initialise(
            self.sernum, self.cfg.product_rev, self.cfg.hardware_rev
        )
        # Save SerialNumber & MAC on a remote server.
        mac = mes["SL_MAC"]().value1
        dev["serialtomac"].blemac_set(self.sernum, mac)

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate Vbatt."""
        smartlink201 = dev["smartlink201"]
        vbatt = mes["dmm_Vbatt"](timeout=5).value1
        # Adjust Pre & Post reading dependant limits
        self.limits["SL_VbattPre"].adjust(nominal=vbatt)
        self.limits["SL_Vbatt"].adjust(nominal=vbatt)
        mes["SL_VbattPre"]()
        smartlink201.vbatt_cal(vbatt)
        mes["SL_Vbatt"]()

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Tank sensors."""
        # Always measure all the inputs, and force a fail if any input
        # has failed. So we get a full dataset on every test.
        with share.MultiMeasurementSummary() as checker:
            smartlink201 = dev["smartlink201"]
            smartlink201.analog_read()  # Read all tank sensor inputs
            with tester.PathName("Open"):
                for index in range(16):  # All analog tank inputs
                    name = console.tank_name(index)
                    with tester.PathName(name):
                        checker.measure(mes[name])
            with tester.PathName("Active"):
                self.relay(  # Pull down alternate inputs
                    (
                        ("rla_s1", True),
                        ("rla_s3", True),
                    ),
                    delay=self.analog_read_wait,
                )
                smartlink201.analog_read()  # Read all tank sensor inputs
                for index in range(16):  # All analog tank inputs
                    name = console.tank_name(index)
                    if not index % 2:  # Every 2nd input is now low
                        name += "_L"
                    with tester.PathName(name):
                        checker.measure(mes[name])


class Devices(share.Devices):
    """Devices."""

    sw_arm_image = None

    def open(self):
        """Create all Instruments."""
        fixture = "035827"
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Vbatt", tester.DCSource, "DCS2"),
            ("dcs_USB", tester.DCSource, "DCS3"),
            ("rla_s1", tester.Relay, "RLA1"),  # 4k7 pull-down on tanks
            ("rla_s2", tester.Relay, "RLA2"),
            ("rla_s3", tester.Relay, "RLA3"),
            ("rla_s4", tester.Relay, "RLA4"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.config.Fixture.port(fixture, "ARM")
        self["progARM"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_arm_image,
            crpmode=False,
            bda4_signals=True,
        )
        # Serial connection to the Nordic console
        smartlink201_ser = serial.Serial(baudrate=115200, timeout=5.0)
        #   Set port separately, as we don't want it opened yet
        smartlink201_ser.port = share.config.Fixture.port(fixture, "NORDIC")
        con_class = {
            "B": console.BLExtenderConsole,
            "S": console.SmartLink201Console,
        }[self.parameter]
        self["smartlink201"] = con_class(smartlink201_ser)
        # Connection to Serial To MAC server
        self["serialtomac"] = share.bluetooth.SerialToMAC()
        # Fixture USB power
        self["dcs_USB"].output(8.0, output=True, delay=10)
        self.add_closer(lambda: self["dcs_USB"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["smartlink201"].close()
        self["dcs_Vbatt"].output(0.0, False)
        for rla in (
            "rla_s1",
            "rla_s2",
            "rla_s3",
            "rla_s4",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_nrf_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["Vin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["Vin"].doc = "Vin rail"
        self["3V3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["3V3"].doc = "3V3 rail"
        self["photosense1"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.1)
        self["photosense1"].doc = "Part detector output"
        self["photosense2"] = sensor.Vdc(dmm, high=7, low=2, rng=100, res=0.1)
        self["photosense2"].doc = "Part detector output"
        self["Vbatt"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self["Vbatt"].doc = "X13 pin 1"
        self["S5tank"] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self["S5tank"].doc = "S5 Tank Type"
        self["SnEntry"] = sensor.DataEntry(
            message=tester.translate("smartlink201_initial", "msgSnEntry"),
            caption=tester.translate("smartlink201_initial", "capSnEntry"),
        )
        self["SnEntry"].doc = "Entered S/N"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_nrf_image,
        )
        # Console sensors
        smartlink201 = self.devices["smartlink201"]
        self["SL_MAC"] = sensor.Keyed(smartlink201, "MAC")
        self["SL_MAC"].doc = "Nordic BLE MAC"
        # Convert "xx:xx:xx:xx:xx:xx(random)" to "xxxxxxxxxxxx"
        self["SL_MAC"].on_read = (
            lambda value: value.replace(":", "").replace(" (random)", "").lower()
        )
        self["SL_Vbatt"] = sensor.Keyed(smartlink201, "BATT")
        self["SL_Vbatt"].doc = "Nordic Vbatt reading"
        self["SL_Vbatt"].scale = 1000
        # Convert "Current Battery Voltage: xxxxx mV" to "xxxxx"
        self["SL_Vbatt"].on_read = lambda value: value.replace(
            "Current Battery Voltage: ", ""
        ).replace(" mV", "")
        for index in range(16):  # 16 analog tank inputs
            name = console.tank_name(index)
            self[name] = sensor.Keyed(smartlink201, name)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_Parts1", "PartOk", "photosense1", "Tank and RJ parts fitted"),
                (
                    "dmm_Parts2",
                    "PartOk",
                    "photosense2",
                    "Connector and switch parts fitted",
                ),
                ("dmm_S5tank", "S5tank", "S5tank", "S5 Tank switch ON"),
                ("dmm_Vin", "Vin", "Vin", "Vin rail ok"),
                ("dmm_3V3", "3V3", "3V3", "3V3 rail ok"),
                ("dmm_Vbatt", "Vbatt", "Vbatt", "Actual Vbatt rail"),
                ("ui_serialnum", "SerNum", "SnEntry", "S/N valid"),
                (
                    "SL_VbattPre",
                    "SL_VbattPre",
                    "SL_Vbatt",
                    "Nordic Vbatt before adjustment",
                ),
                ("SL_Vbatt", "SL_Vbatt", "SL_Vbatt", "Nordic Vbatt after adjustment"),
                ("SL_MAC", "BleMac", "SL_MAC", "Nordic MAC address valid"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
        for index in range(16):  # All tank inputs High
            name = console.tank_name(index)
            self[name] = tester.Measurement(
                self.limits["TankHi"], self.sensors[name], doc="Input open circuit"
            )
            if not index % 2:  # S1,S3 tank inputs Low
                self[name + "_L"] = tester.Measurement(
                    self.limits["TankLo"], self.sensors[name], doc="Input pulled down"
                )
