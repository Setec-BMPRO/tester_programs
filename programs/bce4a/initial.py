#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BCE4A Initial Test Program."""

import pathlib

import libtester
import serial
import tester

import share

class Initial(share.TestSequence):
    """BCE4A Initial Test Program."""
 
    limitdata = (
        libtester.LimitLow("FixtureLock", 200),  # replace 200   to 20 Ask 
    )

    def open(self):
        """Prepare for testing."""
        self.configure(self.limitdata, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Apply input DC and measure voltages."""
        # dev["dcs_Vin"].output(self._vcc_bias_set, output=True)
        dev["dcs_Vin"].output(12.0, output=True, delay=2)
        self.measure(("dmm_vin", "dmm_Vcc", ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""
        """Communicate with the PIC console."""
        pic = dev["pic"]
        pic.open()
        mes["ProgramPIC"]()
    

class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Vin", tester.DCSource, "DCS1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        #Original
        # self["PicKit"] = tester.PicKit(
        #     (self.physical_devices["PICKIT"], self["rla_mic"])
        # )

        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"])
        )

        # Serial connection to the console
        # pic_ser = serial.Serial(baudrate=19200, timeout=2.0)
        # # # Set port separately, as we don't want it opened yet
        # pic_ser.port = self.port("PIC")


    def reset(self):
        """Reset instruments."""
        self["pic"].close()

class Sensors(share.Sensors):
    """Sensors."""
    # Firmware image
    pic_hex_mic = "BCE4A_FW_20250521_Customer_Samples.hex"

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        pic = self.devices["pic"]
        sensor = tester.sensor
        
        # self["Vsec5VuP"] = sensor.Vdc(dmm, high=19, low=1, rng=10, res=0.001)
        # self["SwRev"] = sensor.Keyed(pic, "PIC-SwRev")
        # self["MicroTemp"] = sensor.Keyed(pic, "PIC-MicroTemp")
        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / self.pic_hex_mic,
            "16F684",
        )

        self["lock"] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self["vac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
                ("dmm_vbus", "Vbus", "vbus", ""),

            )
        )
