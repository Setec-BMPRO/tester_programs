#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""IDS-500 Micro Initial Test Program."""

import pathlib

import serial
import tester

import share
from . import config, console


class InitialMicro(share.TestSequence):
    """IDS-500 Initial Micro Test Program."""

    # test limits
    limitdata = (
        tester.LimitDelta("5V", nominal=5.0, delta=0.05),
        tester.LimitRegExp("SwRev", "I,  1, 2,Software Revision"),
        tester.LimitRegExp("MicroTemp", "D, 16,    [0-9]{2},MICRO Temp\.\(C\)"),
    )

    def open(self, uut):
        """Prepare for testing."""
        Sensors.pic_hex_mic = config.pic_hex_mic
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Comms", self._step_comms),
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Apply Vcc and program the board."""
        dev["dcs_vcc"].output(5.0, True)
        self.measure(
            (
                "dmm_vsec5VuP",
                "ProgramPIC",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_comms(self, dev, mes):
        """Communicate with the PIC console."""
        pic = dev["pic"]
        pic.open()
        pic.sw_test_mode()
        pic.expected = 1
        self.measure(
            (
                "swrev",
                "microtemp",
            )
        )


class Devices(share.Devices):
    """Micro Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vcc", tester.DCSource, "DCS1"),
            ("rla_mic", tester.Relay, "RLA10"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_mic"])
        )
        # Serial connection to the console
        pic_ser = serial.Serial(baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = share.config.Fixture.port("017056", "PIC")
        self["pic"] = console.Console(pic_ser)

    def reset(self):
        """Reset instruments."""
        self["pic"].close()
        self["dcs_vcc"].output(0.0, False)
        self["rla_mic"].set_off()


class Sensors(share.Sensors):
    """Micro Sensors."""

    # Firmware image
    pic_hex_mic = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        pic = self.devices["pic"]
        sensor = tester.sensor
        self["Vsec5VuP"] = sensor.Vdc(dmm, high=19, low=1, rng=10, res=0.001)
        self["SwRev"] = sensor.Keyed(pic, "PIC-SwRev")
        self["MicroTemp"] = sensor.Keyed(pic, "PIC-MicroTemp")
        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / self.pic_hex_mic,
            "18F4520",
        )


class Measurements(share.Measurements):
    """Micro Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_vsec5VuP", "5V", "Vsec5VuP", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
                ("swrev", "SwRev", "SwRev", ""),
                ("microtemp", "MicroTemp", "MicroTemp", ""),
            )
        )
