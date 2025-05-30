#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BCE4A Initial Test Program."""

import pathlib

import libtester
import tester

import share

class Initial(share.TestSequence):
    """BCE4A Initial Test Program."""
    
    vin_set = 12.0  # Input DC voltage to power the unit
    vac_set = 220.0  # Input AC voltage
    
    limitdata = (
        libtester.LimitLow("FixtureLock", 200),  # replace 200   to 20 Ask 
        libtester.LimitBetween("Vin", vin_set - 1.0, vin_set, doc="Input voltage present"),
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
        dev["dcs_Vin"].output(self.vin_set, output=True, delay=2)
        # self.measure(("dmm_vin", "dmm_Vcc", ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""
        """Communicate with the PIC console."""
        mes["ProgramPIC"]()
    

class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Vin", tester.DCSource, "DCS2"),
            ("rla_mic", tester.Relay, "RLA1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        #Original
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_mic"])
        )


    def reset(self):
        """Reset instruments."""
        self["dcs_Vin"].output(0.0, False)
        self["rla_mic"].set_off()

class Sensors(share.Sensors):
    """Sensors."""
    # Firmware image
    pic_hex_mic = "BCE4A_FW_20250521_Customer_Samples.hex"

    def open(self):
        """Create all Sensors."""
        # dmm = self.devices["dmm"]
        sensor = tester.sensor

        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / self.pic_hex_mic,
            "16F684",
        )

        # self["lock"] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        # self["vac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                # ("dmm_lock", "FixtureLock", "lock", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
            )
        )
