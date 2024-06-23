#!/usr/bin/env python3
# Copyright 2018 SETEC Pty Ltd
"""CN10[23] / ODL10[13] Initial Test Program.

Shares the test fixture with the ODL104 program.

There are 2 different hardware:
    CN102 & ODL101
    CN103 & ODL103  Front label differs.

"""

import pathlib

import serial
import tester

import share

from . import config, console


class Initial(share.TestSequence):
    """CN10x / ODL10x Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        limits = self.cfg.limits_initial
        Sensors.sw_nordic_image = self.cfg.sw_nordic_image
        Devices.fixture = self.fixture
        Devices.sw_nxp_image = self.cfg.sw_nxp_image
        self.configure(limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("PartCheck", self._step_part_check),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("TestArm", self._step_test_arm),
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
        dev["rla_reset"].set_on()  # Disable ARM to Nordic RESET
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
        """Program the devices."""
        self.devices["progARM"].program()
        mes["JLink"]()

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        dev["rla_reset"].set_off()  # Allow ARM to Nordic RESET
        console = dev["console"]
        console.open()
        console.brand(self.cfg.hw_version, self.uuts[0].sernum, self.cfg.banner_lines)

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        dev["console"]["ADC_SCAN"] = 100
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
        """Test the CAN Bus."""
        mes["cn102_can_bind"](timeout=10)


class Devices(share.Devices):
    """Devices."""

    fixture = None
    sw_nxp_image = None  # ARM software image

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
        # ARM device programmer
        arm_port = share.config.Fixture.port(self.fixture, "ARM")
        self["progARM"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_nxp_image,
            crpmode=False,
            bda4_signals=True,  # Use BDA4 serial lines for RESET & BOOT
        )
        # Serial connection to the console
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = arm_port
        # Console driver
        self["console"] = console.Console(con_ser)

    def reset(self):
        """Test run has stopped."""
        self["console"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in (
            "rla_reset",
            "rla_nxp",
            "rla_temp",
            "rla_s1",
            "rla_s2",
            "rla_s3",
            "rla_s4",
        ):
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
            ("CANBIND", "CAN_BIND"),
            ("tank1", "TANK1"),
            ("tank2", "TANK2"),
            ("tank3", "TANK3"),
            ("tank4", "TANK4"),
        ):
            self[name] = sensor.Keyed(console, cmdkey)
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject.projectfile("nrf52832"),
            pathlib.Path(__file__).parent / self.sw_nordic_image,
        )


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
                ("cn102_can_bind", "CAN_BIND", "CANBIND", ""),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
