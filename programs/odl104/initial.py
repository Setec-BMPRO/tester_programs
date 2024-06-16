#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Initial Test Program.

Shares the test fixture with the CN102 program.

"""

import pathlib
import time

import tester

import share

from . import config, console


class Initial(share.TestSequence):
    """ODL104 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        limits = self.cfg.limits_initial
        Sensors.sw_nordic_image = self.cfg.sw_nordic_image
        super().configure(limits, Devices, Sensors, Measurements)
        super().open(uut)
        self.steps = (
            tester.TestStep("PartCheck", self._step_part_check),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Nordic", self._step_nordic),
            tester.TestStep("TankSense", self._step_tank_sense),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_part_check(self, dev, mes):
        """Measure Part detection microswitches."""
        self.measure(("dmm_microsw", "dmm_sw1", "dmm_sw2"), timeout=5)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["rla_nxp"].set_on()  # Disconnect BDA4 Tx/Rx from ARM
        dev["dcs_vin"].output(8.6, output=True)
        self.measure(
            (
                "dmm_vin",
                "dmm_3v3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the Nordic BLE module."""
        mes["JLink"]()
        # Wait for the ARM Device to be programmed by the Nordic module
        # LED quickly flashes white while this happens
        time.sleep(5)

    @share.teststep
    def _step_nordic(self, dev, mes):
        """Test the Nordic device."""
        console = dev["console"]
        console.open()
        sernum = self.uuts[0].sernum
        console.brand(self.cfg.hw_version, sernum, self.cfg.banner_lines)
        # Save SerialNumber & MAC on a remote server.
        mac = mes["ble_mac"]().value1
        dev["serialtomac"].blemac_set(sernum, mac)

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        time.sleep(0.5)
        self.relay(
            (
                ("rla_s1", True),
                ("rla_s2", True),
                ("rla_s3", True),
                ("rla_s4", True),
            ),
            delay=0.2,
        )
        self.measure(
            ("tank1_level", "tank2_level", "tank3_level", "tank4_level"), timeout=5
        )

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        with dev["canreader"]:
            mes["can_active"](timeout=10)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("rla_reset", tester.Relay, "RLA1"),  # 1k RESET to 3V3
            ("rla_nxp", tester.Relay, "RLA2"),  # Disconnect NXP Tx/Rx
            ("rla_temp", tester.Relay, "RLA3"),  # Temp Sensor pull down
            ("rla_s1", tester.Relay, "RLA4"),
            ("rla_s2", tester.Relay, "RLA5"),
            ("rla_s3", tester.Relay, "RLA6"),
            ("rla_s4", tester.Relay, "RLA7"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        port = tester.RttPort()
        self["console"] = console.Console(port)
        # CAN devices
        self["canreader"] = tester.CANReader(self.physical_devices["CAN"])
        self["candetector"] = share.can.PacketDetector(self["canreader"])
        # Connection to Serial To MAC server
        self["serialtomac"] = share.bluetooth.SerialToMAC()

    def run(self):
        """Test run is starting."""
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["canreader"].stop()
        self["console"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in ("rla_nxp", "rla_temp", "rla_s1", "rla_s2", "rla_s3", "rla_s4"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    sw_nordic_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oVin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["o3V3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["sw1"] = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self["sw2"] = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self["microsw"] = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        console = self.devices["console"]
        for name, cmdkey in (
            ("tank1", "TANK1"),
            ("tank2", "TANK2"),
            ("tank3", "TANK3"),
            ("tank4", "TANK4"),
        ):
            self[name] = sensor.Keyed(console, cmdkey)
        # Convert tank readings from zero to one based
        for name in ("tank1", "tank2", "tank3", "tank4"):
            self[name].on_read = lambda value: value + 1
        self["BleMac"] = sensor.Keyed(console, "MAC")
        self["BleMac"].doc = "Nordic BLE MAC"
        # Convert "xx:xx:xx:xx:xx:xx (random)" to "xxxxxxxxxxxx"
        self["BleMac"].on_read = (
            lambda value: value.replace(":", "").replace(" (random)", "").lower()
        )
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_nordic_image,
        )
        self["cantraffic"] = sensor.Keyed(self.devices["candetector"], None)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_microsw", "Part", "microsw", ""),
                ("dmm_sw1", "Part", "sw1", ""),
                ("dmm_sw2", "Part", "sw2", ""),
                ("dmm_vin", "Vin", "oVin", ""),
                ("dmm_3v3", "3V3", "o3V3", ""),
                ("tank1_level", "Tank", "tank1", ""),
                ("tank2_level", "Tank", "tank2", ""),
                ("tank3_level", "Tank", "tank3", ""),
                ("tank4_level", "Tank", "tank4", ""),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
                ("ble_mac", "BleMac", "BleMac", "MAC address"),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
            )
        )
