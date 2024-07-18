#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd.
"""DCX Initial Test Programs."""

import pathlib

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):
    """Initial Test Programs."""

    def open(self):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        Devices.sw_image = self.cfg.values.sw_image
        Sensors.outputs = self.cfg.outputs
        self.configure(self.cfg.limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise_arm),
            tester.TestStep("Calibrate", self._step_calibrate),
            tester.TestStep("Output", self._step_output),
            tester.TestStep("RemoteSw", self._step_remote_sw),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        dev["dcs_vbat"].output(self.cfg.vbat_in, True)
        self.measure(("FixtureLock", "dmm_vbat", "dmm_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev["programmer"].program()

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device."""
        con = dev["con"]
        con.open()
        con.brand(self.cfg.values.hw_version, self.uuts[0].sernum, dev["rla_reset"])
        con.manual_mode()

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibration."""
        con = dev["con"]
        v_actual = self.measure(("dmm_vbat",), timeout=10).value1
        con["VBUS_CAL"] = v_actual  # Calibrate Vout reading
        con["NVWRITE"] = True

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches."""
        con = dev["con"]
        con.load_set(set_on=True, loads=())  # All outputs OFF
        mes["ui_yesnored"](timeout=5)
        dev["dcl_out"].output(1.0, True)  # A little load on the output.
        mes["dmm_vloadoff"](timeout=5)
        con.load_set(set_on=False, loads=())  # All outputs ON
        mes["ui_yesnogreen"](timeout=5)
        # Always measure all the outputs, and force a fail if any output
        # has failed. So we get a full dataset on every test.
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(self.cfg.outputs):
                con.load_set(set_on=True, loads=[load])  # One outputs ON
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["arm_loads"][load])
                con.load_set(set_on=True, loads=())  # All outputs OFF
        con.load_set(set_on=False, loads=())  # All outputs ON

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Test Remote Load Isolator Switch."""
        with dev["rla_loadsw"]:
            mes["arm_remote"](timeout=5)
        mes["dmm_vload"](timeout=5)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        dev["con"]["CAN_PWR_EN"] = True
        self.measure(("dmm_canpwr", "arm_can_bind"), timeout=10)


class Devices(share.Devices):
    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vcom", tester.DCSource, "DCS1"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("dcl_out", tester.DCLoad, "DCL1"),
            ("dcl_bat", tester.DCLoad, "DCL5"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
            ("rla_loadsw", tester.Relay, "RLA4"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        arm_port = self.port("ARM")
        self["programmer"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_image,
            crpmode=False,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = arm_port
        self["con"] = console.Console(con_ser)
        # Switch on power to fixture circuits
        self["dcs_vcom"].output(9.0, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_vcom"].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self["con"].close()
        for dev in ("dcs_vbat", "dcl_out", "dcl_bat"):
            self[dev].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_loadsw"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    outputs = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vload"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["vload"].doc = "All Load outputs combined"
        self["vbat"] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self["vbat"].doc = "Battery output"
        self["o3v3"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["o3v3"].doc = "U307 Output"
        self["lock"] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self["lock"].doc = "Microswitch contacts"
        self["canpwr"] = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self["canpwr"].doc = "X303"
        self["yesnored"] = sensor.YesNo(
            message=tester.translate("bp35_initial", "IsOutputLedRed?"),
            caption=tester.translate("bp35_initial", "capOutputLed"),
        )
        self["yesnored"].doc = "Tester operator"
        self["yesnogreen"] = sensor.YesNo(
            message=tester.translate("bp35_initial", "IsOutputLedGreen?"),
            caption=tester.translate("bp35_initial", "capOutputLed"),
        )
        self["yesnogreen"].doc = "Tester operator"
        con = self.devices["con"]
        for name, cmdkey, units in (
            ("arm_sect", "SEC_T", "°C"),
            ("arm_vout", "BUS_V", "V"),
            ("arm_canbind", "CAN_BIND", ""),
            ("arm_vbat", "BATT_V", "V"),
            ("arm_ibat", "BATT_I", "A"),
            ("arm_vout_ov", "VOUT_OV", ""),
            ("arm_remote", "BATT_SWITCH", ""),
        ):
            self[name] = sensor.Keyed(con, cmdkey)
            if units:
                self[name].units = units
        loads = []  # Generate load current sensors
        for i in range(1, self.outputs + 1):
            loads.append(sensor.Keyed(con, "LOAD_{0}".format(i)))
        self["arm_loads"] = loads


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("FixtureLock", "FixtureLock", "lock", "Fixture lid closed"),
                ("dmm_vload", "Vload", "vload", "Outputs on"),
                ("dmm_vloadoff", "VloadOff", "vload", "Outputs off"),
                ("dmm_vbat", "Vbat", "vbat", "Injected Vbatt voltage"),
                ("dmm_3v3", "3V3", "o3v3", "3V3 rail voltage"),
                ("ui_yesnored", "Notify", "yesnored", "LED Red"),
                ("ui_yesnogreen", "Notify", "yesnogreen", "LED Green"),
                ("arm_sect", "ARM-SecT", "arm_sect", "Temperature"),
                ("arm_vout", "ARM-Vout", "arm_vout", "Vbatt"),
                ("dmm_canpwr", "CanPwr", "canpwr", "CAN bus rail voltage"),
                ("arm_can_bind", "CAN_BIND", "arm_canbind", "CAN bound"),
                ("arm_vbat", "Vbat", "arm_vbat", "Battery voltage"),
                ("arm_ibat", "ARM-BattI", "arm_ibat", "Battery current"),
                ("arm_vout_ov", "Vout_OV", "arm_vout_ov", "Vout OVP"),
                ("arm_remote", "ARM-RemoteClosed", "arm_remote", "Remote input"),
            )
        )
        loads = []  # Generate load current measurements
        for sen in self.sensors["arm_loads"]:
            loads.append(tester.Measurement(self.limits["ARM-LoadI"], sen))
        self["arm_loads"] = loads
