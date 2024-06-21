#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd
"""BSGateway Initial Test Program."""

import pathlib

import libtester
import serial
import tester

import share
from . import console


class Initial(share.TestSequence):
    """Initial Test Program."""

    _pre_release = "bsgateway_v1.0.4-0-g794a95c.hex"
    sw_image = {  # Key: Revision, Value: Image filename
        None: _pre_release,
        "1": _pre_release,
        "2": None,
    }
    v_set = 12.0  # Input DC voltage to power the unit
    testlimits = (  # Test limits
        libtester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
    )

    def open(self):
        """Prepare for testing."""
        Devices.fixture = self.fixture
        Sensors.sw_image = self.sw_image[self.uuts[0].revision]
        super().configure(self.testlimits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Calibrate", self._step_calibrate),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up the unit."""
        for dcs in ("dcs_vin", "dcs_can"):
            dev[dcs].output(self.v_set, True)
        self.measure(("dev_3v3", "can_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        mes["JLink"]()

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate the unit."""
        con = dev["console"]
        con.open()
        con.pre_calibrate()
        rla = dev["rla_cal"]
        rla.set_on(delay=0.1)
        offacc = con.cali()
        rla.set_off(delay=0.1)
        iacc = con.cali()
        vcc = mes["dev_3v3"]().value1
        con.calibrate(vcc, offacc, iacc)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        with dev["canreader"]:
            mes["can_active"]()


class Devices(share.Devices):
    """Devices."""

    fixture = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS1"),
            ("dcs_can", tester.DCSource, "DCS2"),
            ("rla_cal", tester.Relay, "RLA1"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        con_ser = serial.Serial()
        # Set port separately - don't open until after programming
        con_ser.port = share.config.Fixture.port(self.fixture, "ARM")
        self["console"] = console.Console(con_ser)
        self["can"] = self.physical_devices["CAN"]
        # CAN traffic reader
        self["canreader"] = tester.CANReader(self.physical_devices["CAN"])
        # CAN traffic detector
        self["candetector"] = share.can.PacketDetector(self["canreader"])

    def run(self):
        """Test run is starting."""
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["canreader"].stop()
        self["console"].close()
        for dcs in ("dcs_vin", "dcs_can"):
            self[dcs].output(0.0, False)
        self["rla_cal"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_image = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["dev_3v3"] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.01)
        self["dev_3v3"].doc = "U1 output"
        self["can_3v3"] = sensor.Vdc(dmm, high=2, low=2, rng=10, res=0.01)
        self["can_3v3"].doc = "U6 output"
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("r7fa2l1a9"),
            pathlib.Path(__file__).parent / self.sw_image,
        )
        self["cantraffic"] = sensor.Keyed(self.devices["candetector"], None)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dev_3v3", "3V3", "dev_3v3", "3V3 rail voltage"),
                ("can_3v3", "3V3", "can_3v3", "CAN 3V3 rail voltage"),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
            )
        )
