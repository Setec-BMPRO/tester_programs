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
        Sensors.iload = self.cfg.iload
        self.configure(self.cfg.limits, Devices, Sensors, Measurements)
        super().open()
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise_arm),
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("Output", self._step_output),
            tester.TestStep("RemoteSw", self._step_remote_sw),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals to power up the ARM.

        """
        self.measure(
            (
                "dmm_lock",
            ),
            timeout=5,
        )
        dev["dcs_vbat"].output(self.cfg.vbat_in, True)
        self.measure(("dmm_vbatin", "dmm_3v3"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM & PIC devices."""
        dev["program_arm"].program_begin()  # Program ARM in background
        try:
            if not self.cfg.is_pm:
                dev["SR_LowPower"].output(self.cfg.sr_vin, output=True)
                mes["dmm_solarvcc"](timeout=5)
                mes["program_pic"]()
                dev["SR_LowPower"].output(0.0)
        except Exception:
            raise
        finally:
            dev["program_arm"].program_wait()  # Wait for ARM programming
        # Cold Reset microprocessor for units that were already programmed
        # (Pulsing RESET isn't enough to reconfigure the I/O circuits)
        dcsource, load = dev["dcs_vbat"], dev["dcl_bat"]
        dcsource.output(0.0)
        load.output(1.0, delay=0.5)
        load.output(0.0)
        dcsource.output(self.cfg.vbat_in)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        con = dev["con"]
        con.open()
        con.brand(
            self.cfg.values.hw_version,
            self.uuts[0].sernum,
            dev["rla_reset"],
        )

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with AC."""
        con = dev["con"]
        con.power_on()
        mes["arm_vout_ov"]()
        dev["dcs_vbat"].output(0.0, output=False)
        mes["arm_vout_ov"]()
        self.measure(("dmm_3v3", "dmm_15vs"), timeout=10)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches."""
        con = dev["con"]
        # All outputs OFF
        con.load_set(set_on=True, loads=())
        mes["ui_yesnored"](timeout=5)
        # A little load on the output.
        dev["dcl_out"].output(1.0, True)
        mes["dmm_vloadoff"](timeout=5)
        # All outputs ON
        con.load_set(set_on=False, loads=())
        mes["ui_yesnogreen"](timeout=5)

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
        self.measure(
            (
                "dmm_canpwr",
                "arm_can_bind",
            ),
            timeout=10,
        )


class Devices(share.Devices):
    """Devices."""

    arm_image = None  # ARM software image

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vcom", tester.DCSource, "DCS1"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("dcs_vaux", tester.DCSource, "DCS3"),
            ("dcl_out", tester.DCLoad, "DCL1"),
            ("dcl_bat", tester.DCLoad, "DCL5"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
            ("rla_loadsw", tester.Relay, "RLA4"),
            ("rla_acsw", tester.Relay, "RLA6"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_pic"])
        )
        # Device programmer
        arm_port = self.port("ARM")
        self["program_arm"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.arm_image,
            crpmode=False,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        # Serial connection to the console
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = arm_port
        # BP35 Console driver
        self["con"] = console.Console(con_ser)
        # Switch on power to fixture circuits
        self["dcs_vcom"].output(9.0, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_vcom"].output(0.0, output=False))
        self["ard"].open()
        self.add_closer(lambda: self["ard"].close())

    def reset(self):
        """Reset instruments."""
        self["con"].close()
        # Switch off AC Source & discharge the unit
        self["dcl_bat"].output(2.0, delay=1)
        for dev in ("dcs_vbat", "dcs_vaux", "dcl_out", "dcl_bat"):
            self[dev].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_loadsw", "rla_acsw"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    outputs = None  # Number of outputs
    iload = None  # Load current

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["vload"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["vload"].doc = "All Load outputs combined"
        self["vbat"] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self["vbat"].doc = "Battery output"
        self["vset"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["vset"].doc = "Between TP308,9 and Vout"
        self["o3v3"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["o3v3"].doc = "U307 Output"
        self["o15vs"] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self["o15vs"].doc = "Across C312"
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
        # Console sensors
        con = self.devices["con"]
        for name, cmdkey, units in (
            ("arm_sect", "SEC_T", "°C"),
            ("arm_vout", "BUS_V", "V"),
            ("arm_canbind", "CAN_BIND", ""),
            ("arm_vbat", "BATT_V", "V"),
            ("arm_ibat", "BATT_I", "A"),
            ("arm_vout_ov", "VOUT_OV", ""),
            ("arm_iout", "SR_IOUT", "A"),
            ("arm_remote", "BATT_SWITCH", ""),
        ):
            self[name] = sensor.Keyed(con, cmdkey)
            if units:
                self[name].units = units
        # Generate load current sensors
        loads = []
        for i in range(1, self.outputs + 1):
            loads.append(sensor.Keyed(con, "LOAD_{0}".format(i)))
        self["arm_loads"] = loads


class Measurements(share.Measurements):
    """Measurements."""

    is_pm = None

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", "Fixture lid closed"),
                ("dmm_15vs", "15Vs", "o15vs", "Secondary 15V rail"),
                ("dmm_vload", "Vload", "vload", "Outputs on"),
                ("dmm_vloadoff", "VloadOff", "vload", "Outputs off"),
                ("dmm_vbatin", "VbatIn", "vbat", "Injected Vbatt voltage"),
                ("dmm_vbat", "Vbat", "vbat", "Vbatt output voltage"),
                ("dmm_vaux", "Vaux", "vbat", "Vaux output voltage"),
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
        # Generate load current measurements
        loads = []
        for sen in self.sensors["arm_loads"]:
            loads.append(tester.Measurement(self.limits["ARM-LoadI"], sen))
        self["arm_loads"] = loads
