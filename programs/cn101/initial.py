#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""CN101 Initial Test Program."""

import pathlib

import serial

import share
import tester

from . import config, console


class Initial(share.TestSequence):
    """CN101 Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        Devices.fixture = self.fixture
        Devices.sw_version = self.cfg.sw_version
        self.configure(self.cfg.limits_initial, Devices, Sensors, Measurements)
        super().open()
        self.limits["SwVer"].adjust(
            "^{0}$".format(self.cfg.sw_version.replace(".", r"\."))
        )
        self.steps = (
            tester.TestStep("PartCheck", self._step_part_check),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self.devices["programmer"].program),
            tester.TestStep("TestArm", self._step_test_arm),
            tester.TestStep("TankSense", self._step_tank_sense),
            tester.TestStep("Bluetooth", self._step_bluetooth),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_part_check(self, dev, mes):
        """Measure Part detection microswitches."""
        self.measure(("dmm_microsw", "dmm_sw1", "dmm_sw2"), timeout=5)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev["dcs_vin"].output(8.6, output=True)
        self.measure(
            (
                "dmm_vin",
                "dmm_3v3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        dev["cn101"].open()
        dev["cn101"].brand(
            self.cfg.hw_version, self.uuts[0].sernum, self.cfg.banner_lines
        )
        mes["cn101_swver"]()

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        dev["cn101"]["ADC_SCAN"] = 100
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
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev["dcs_vin"].output(0.0, delay=1.0)
        dev["dcs_vin"].output(12.0, delay=15.0)
        btmac = share.MAC.loads(mes["cn101_btmac"]().value1)
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac.dumps())
        reply = dev["pi_bt"].scan_advert_blemac(btmac.dumps(separator=""), timeout=20)
        reply = reply is not None  # To boolean
        self._logger.debug("Bluetooth MAC detected: %s", reply)
        mes["detectBT"].sensor.store(reply)
        mes["detectBT"]()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes["cn101_can_bind"](timeout=10)
        cn101tunnel = dev["cn101tunnel"]
        cn101tunnel.open()
        mes["TunnelSwVer"]()
        cn101tunnel.close()


class Devices(share.Devices):
    """Devices."""

    fixture = None
    sw_version = None  # ARM software version

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS2"),
            ("rla_s1", tester.Relay, "RLA4"),
            ("rla_s2", tester.Relay, "RLA5"),
            ("rla_s3", tester.Relay, "RLA6"),
            ("rla_s4", tester.Relay, "RLA7"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.config.Fixture.port(self.fixture, "ARM")
        sw_file = "cn101_{0}.bin".format(self.sw_version)
        self["programmer"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / sw_file,
            crpmode=False,
            bda4_signals=True,  # Use BDA4 serial lines for RESET & BOOT
        )
        # Serial connection to the console
        cn101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        cn101_ser.port = arm_port
        # CN101 Console driver
        self["cn101"] = console.DirectConsole(cn101_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices["CAN"], share.can.SETECDeviceID.CN101.value
        )
        self["cn101tunnel"] = console.TunnelConsole(tunnel)
        # Connection to RaspberryPi bluetooth server
        self["pi_bt"] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url()
        )

    def reset(self):
        """Reset instruments."""
        self["cn101"].close()
        self["cn101tunnel"].close()
        self["dcs_vin"].output(0.0, False)
        for rla in (
            "rla_s1",
            "rla_s2",
            "rla_s3",
            "rla_s4",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oMirBT"] = sensor.Mirror()
        self["microsw"] = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self["sw1"] = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self["sw2"] = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        self["oVin"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["o3V3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        # Console sensors
        cn101 = self.devices["cn101"]
        cn101tunnel = self.devices["cn101tunnel"]
        for name, cmdkey in (
            ("oCANBIND", "CAN_BIND"),
            ("tank1", "TANK1"),
            ("tank2", "TANK2"),
            ("tank3", "TANK3"),
            ("tank4", "TANK4"),
        ):
            self[name] = sensor.Keyed(cn101, cmdkey)
        for device, name, cmdkey in (
            (cn101, "oSwVer", "SW_VER"),
            (cn101, "oBtMac", "BT_MAC"),
            (cn101tunnel, "TunnelSwVer", "SW_VER"),
        ):
            self[name] = sensor.Keyed(device, cmdkey)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_microsw", "Part", "microsw", ""),
                ("dmm_sw1", "Part", "sw1", ""),
                ("dmm_sw2", "Part", "sw2", ""),
                ("detectBT", "DetectBT", "oMirBT", ""),
                ("dmm_vin", "Vin", "oVin", ""),
                ("dmm_3v3", "3V3", "o3V3", ""),
                ("cn101_swver", "SwVer", "oSwVer", ""),
                ("cn101_btmac", "BtMac", "oBtMac", ""),
                ("tank1_level", "Tank", "tank1", ""),
                ("tank2_level", "Tank", "tank2", ""),
                ("tank3_level", "Tank", "tank3", ""),
                ("tank4_level", "Tank", "tank4", ""),
                ("cn101_can_bind", "CAN_BIND", "oCANBIND", ""),
                ("TunnelSwVer", "SwVer", "TunnelSwVer", ""),
            )
        )
