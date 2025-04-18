#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""BP35 / BP35-II Initial Test Programs."""

import pathlib
import time

import libtester
import serial
import tester

import share
from . import arduino, console, config


class Initial(share.TestSequence):
    """BP35 / BP35-II Initial Test Programs."""

    def open(self):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        limits = self.cfg.limits_initial()
        if self.cfg.is_2:
            arm_image = "bp35II_{0}.bin".format(self.cfg.arm_sw_version)
        else:
            arm_image = "bp35_{0}.bin".format(self.cfg.arm_sw_version)
        Devices.arm_image = arm_image
        Sensors.outputs = self.cfg.outputs
        Sensors.iload = self.cfg.iload
        Sensors.pic_image = "bp35sr_{0}.hex".format(self.cfg.pic_sw_version)
        Measurements.is_pm = self.cfg.is_pm
        self.configure(limits, Devices, Sensors, Measurements)
        super().open()
        if self.cfg.is_pm:
            self.devices["PmTimer"].interval = self.cfg.pm_zero_wait
        self.limits["ARM-SwVer"].adjust(
            "^{0}$".format(self.cfg.arm_sw_version.replace(".", r"\."))
        )
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise_arm),
            tester.TestStep("SrSolar", self._step_sr_solar, not self.cfg.is_pm),
            tester.TestStep("Aux", self._step_aux),
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("Output", self._step_output),
            tester.TestStep("RemoteSw", self._step_remote_sw),
            tester.TestStep("PmSolar", self._step_pm_solar, self.cfg.is_pm),
            tester.TestStep("OCP", self._step_ocp),
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
                "hardware8",
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
        if not self.cfg.is_pm:
            dev["SR_LowPower"].output(self.cfg.sr_vin)
        bp35 = dev["bp35"]
        bp35.open()
        bp35.brand(
            self.cfg.arm_hw_version,
            self.uuts[0].sernum,
            dev["rla_reset"],
            self.cfg.is_pm,
            self.cfg.pic_hw_version,
        )
        if self.cfg.is_pm:
            bp35["PM_RELAY"] = False
            time.sleep(0.5)
            bp35["PM_RELAY"] = True
            dev["PmTimer"].start()
        bp35.manual_mode(start=True)  # Start the change to manual mode
        bp35["FAN"] = 0

    @share.teststep
    def _step_sr_solar(self, dev, mes):
        """Test & Calibrate the Solar Regulator board."""
        bp35 = dev["bp35"]
        dev["SR_HighPower"].on()
        dev["SR_LowPower"].output(0.0, output=False)
        self.measure(
            (
                "arm_sr_alive",
                "arm_vout_ov",
            ),
            timeout=5,
        )
        # The SR needs V & I set to zero after power up or it won't start.
        bp35.sr_set(0, 0)
        # Now set the actual output settings
        bp35.sr_set(self.cfg.sr_vset, self.cfg.sr_iset, delay=2)
        bp35["VOUT_OV"] = 2  # Reset OVP Latch because of Solar overshoot
        # Read solar input voltage and patch measurement limits
        sr_vin = mes["dmm_solarvin"](timeout=5).value1
        mes["arm_sr_vin_pre"].testlimit = (
            libtester.LimitPercent(
                "ARM-SolarVin-Pre", sr_vin, self.cfg.sr_vin_pre_percent
            ),
        )
        mes["arm_sr_vin_post"].testlimit = (
            libtester.LimitPercent(
                "ARM-SolarVin-Post", sr_vin, self.cfg.sr_vin_post_percent
            ),
        )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        self.measure(
            (
                "arm_sr_error",
                "arm_sr_relay",
                "arm_sr_vin_pre",
            ),
            timeout=5,
        )
        # Wait for the voltage to settle
        vmeasured = mes["dmm_vsetpre"].stable(self.cfg.sr_vset_settle).value1
        bp35["SR_VCAL"] = vmeasured  # Calibrate output voltage setpoint
        bp35["SR_VIN_CAL"] = sr_vin  # Calibrate input voltage reading
        # Solar sw ver 182 will not change the setpoint until a DIFFERENT
        # voltage setpoint is given...
        bp35.sr_set(self.cfg.sr_vset - 0.05, self.cfg.sr_iset, delay=0.2)
        bp35.sr_set(self.cfg.sr_vset, self.cfg.sr_iset, delay=1)
        self.measure(
            (
                "arm_sr_vin_post",
                "dmm_vsetpost",
            )
        )
        dev["dcl_bat"].output(self.cfg.sr_ical, output=True, delay=0.5)
        mes["arm_ioutpre"](timeout=5)
        bp35["SR_ICAL"] = self.cfg.sr_ical  # Calibrate current setpoint
        time.sleep(1)
        mes["arm_ioutpost"](timeout=5)
        dev["dcl_bat"].output(0.0)
        dev["SR_HighPower"].off()

    @share.teststep
    def _step_aux(self, dev, mes):
        """Apply Auxiliary input."""
        bp35, source, load = dev["bp35"], dev["dcs_vaux"], dev["dcl_bat"]
        source.output(self.cfg.vaux_in, output=True)
        load.output(0.5, delay=1.0)
        mes["dmm_vbatin"](timeout=1)
        bp35["AUX_RELAY"] = True
        self.measure(("dmm_vaux", "arm_vaux", "arm_iaux"), timeout=5)
        bp35["AUX_RELAY"] = False
        source.output(0.0, output=False)
        load.output(0.0)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with AC."""
        bp35 = dev["bp35"]
        # Complete the change to manual mode
        bp35.manual_mode(vout=self.cfg.vout_set, iout=self.cfg.ocp_set)
        dev["acsource"].output(voltage=self.cfg.vac, output=True)
        self.measure(("dmm_acin", "dmm_pri12v"), timeout=10)
        bp35.power_on()
        # Wait for PFC overshoot to settle
        mes["dmm_vpfc"].stable(self.cfg.pfc_stable)
        mes["arm_vout_ov"]()
        # Remove injected Battery voltage
        dev["dcs_vbat"].output(0.0, output=False)
        mes["arm_vout_ov"]()
        # Is it now running on it's own?
        self.measure(("dmm_3v3", "dmm_15vs"), timeout=10)
        v_actual = self.measure(("dmm_vbat",), timeout=10).value1
        bp35["VSET_CAL"] = v_actual  # Calibrate Vout setting and reading
        bp35["VBUS_CAL"] = v_actual
        bp35["NVWRITE"] = True

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches."""
        bp35 = dev["bp35"]
        # All outputs OFF
        bp35.load_set(set_on=True, loads=())
        mes["ui_yesnored"](timeout=5)
        # A little load on the output.
        dev["dcl_out"].output(1.0, True)
        mes["dmm_vloadoff"](timeout=5)
        # All outputs ON
        bp35.load_set(set_on=False, loads=())
        mes["ui_yesnogreen"](timeout=5)

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Test Remote Load Isolator Switch."""
        with dev["rla_loadsw"]:
            mes["arm_remote"](timeout=5)
        mes["dmm_vload"](timeout=5)

    @share.teststep
    def _step_pm_solar(self, dev, mes):
        """PM type Solar regulator."""
        bp35 = dev["bp35"]
        dev["PmTimer"].wait()
        self.measure(
            (
                "arm_pm_alive",
                "arm_pm_iz_pre",
            )
        )
        bp35["PM_ZEROCAL"] = 0
        bp35["NVWRITE"] = True
        mes["arm_pm_iz_post"]()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test functions of the unit."""
        bp35 = dev["bp35"]
        self.measure(
            ("arm_acv", "arm_acf", "arm_sect", "arm_vout", "arm_fan", "dmm_fanoff"),
            timeout=5,
        )
        bp35["FAN"] = 100
        mes["dmm_fanon"](timeout=5)
        dev["dcl_out"].binary(1.0, self.cfg.iload, 5.0)
        dev["dcl_bat"].output(self.cfg.ibatt, output=True)
        self.measure(
            (
                "dmm_vbat",
                "arm_vbat",
                "arm_ibat",
                "arm_ibus",
            ),
            timeout=5,
        )
        bp35["BUS_ICAL"] = self.cfg.iload + self.cfg.ibatt  # Calibrate current reading
        # Always measure all the outputs, and force a fail if any output
        # has failed. So we get a full dataset on every test.
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(self.cfg.outputs):
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["arm_loads"][load])
        ocp_actual = mes["ramp_ocp_pre"]().value1
        # Adjust current setpoint
        bp35["OCP_CAL"] = round(bp35.ocp_cal() * ocp_actual / self.cfg.ocp_set)
        bp35["NVWRITE"] = True
        mes["ramp_ocp"]()
        dev["dcl_out"].output(0.0)
        dev["dcl_bat"].output(0.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        dev["bp35"]["CAN_PWR_EN"] = True
        self.measure(
            (
                "dmm_canpwr",
                "arm_can_bind",
            ),
            timeout=10,
        )
        bp35tunnel = dev["bp35tunnel"]
        bp35tunnel.open()
        mes["TunnelSwVer"]()
        bp35tunnel.close()


class SrHighPower:
    """High power source to power the SR Solar Regulator.

    It is a BCE282-24 (modified for 20V output) inside the fixture which is
    powered by the AC Source. A relay feeds the AC Source to either the
    BCE282 (ON) or to the BP35 (OFF).

    """

    def __init__(self, relay, acsource):
        """Create the High Power source."""
        self.relay = relay
        self.acsource = acsource

    def on(self):
        """Switch on the source."""
        self.relay.set_on()
        self.acsource.output(voltage=240, output=True, delay=1.0)


    def off(self):
        """Switch off the source."""
        self.acsource.output(voltage=0.0)
        self.relay.set_off()


class Devices(share.Devices):
    """Devices."""

    arm_image = None  # ARM software image

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_vcom", tester.DCSource, "DCS1"),
            ("dcs_vbat", tester.DCSource, "DCS2"),
            ("dcs_vaux", tester.DCSource, "DCS3"),
            ("SR_LowPower", tester.DCSource, "DCS4"),
            ("dcl_out", tester.DCLoad, "DCL1"),
            ("dcl_bat", tester.DCLoad, "DCL5"),
            ("rla_reset", tester.Relay, "RLA1"),
            ("rla_boot", tester.Relay, "RLA2"),
            ("rla_pic", tester.Relay, "RLA3"),
            ("rla_loadsw", tester.Relay, "RLA4"),
            ("rla_acsw", tester.Relay, "RLA6"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_pic"])
        )
        # ARM device programmer
        arm_port = self.port("ARM")
        self["program_arm"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.arm_image,
            crpmode=False,
            boot_relay=self["rla_boot"],
            reset_relay=self["rla_reset"],
        )
        # Serial connection to the BP35 console
        bp35_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bp35_ser.port = arm_port
        # BP35 Console driver
        self["bp35"] = console.DirectConsole(bp35_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices["CAN"], share.can.SETECDeviceID.BP35.value
        )
        self["bp35tunnel"] = console.TunnelConsole(tunnel)
        # High power source for the SR Solar Regulator
        self["SR_HighPower"] = SrHighPower(self["rla_acsw"], self["acsource"])
        self["PmTimer"] = share.BackgroundTimer(1)
#        # Serial connection to the Arduino console
#        ard_ser = serial.Serial(baudrate=115200, timeout=20.0)
#        # Set port separately, as we don't want it opened yet
#        ard_ser.port = self.port("ARDUINO")
#        self["ard"] = arduino.Arduino(ard_ser)
        # Switch on power to fixture circuits
        self["dcs_vcom"].output(9.0, output=True, delay=5.0)
        self.add_closer(lambda: self["dcs_vcom"].output(0.0, output=False))
#        self["ard"].open()
#        self.add_closer(lambda: self["ard"].close())

    def reset(self):
        """Reset instruments."""
        self["bp35"].close()
        self["bp35tunnel"].close()
        self["PmTimer"].stop()
        # Switch off AC Source & discharge the unit
        self["acsource"].reset()
        self["dcl_bat"].output(2.0, delay=1)
        self["discharge"].pulse()
        for dev in ("dcs_vbat", "dcs_vaux", "SR_LowPower", "dcl_out", "dcl_bat"):
            self[dev].output(0.0, False)
        for rla in ("rla_reset", "rla_boot", "rla_pic", "rla_loadsw", "rla_acsw"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    outputs = None  # Number of outputs
    iload = None  # Load current
    pic_image = None  # PIC software image

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["acin"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["acin"].doc = "Across C101"
        self["vpfc"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self["vpfc"].doc = "Voltage on C111"
        self["vload"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["vload"].doc = "All Load outputs combined"
        self["vbat"] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self["vbat"].doc = "Battery output"
        self["vset"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["vset"].doc = "Between TP308,9 and Vout"
        self["pri12v"] = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self["pri12v"].doc = "Across C213"
        self["o3v3"] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self["o3v3"].doc = "U307 Output"
        self["fan"] = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self["fan"].doc = "Across C402"
        self["hardware"] = sensor.Res(dmm, high=8, low=4, rng=100000, res=1)
        self["hardware"].doc = "Across R631"
        self["o15vs"] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self["o15vs"].doc = "Across C312"
        self["lock"] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self["lock"].doc = "Microswitch contacts"
        self["solarvcc"] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self["solarvcc"].doc = "TP301"
        self["solarvin"] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self["solarvin"].doc = "TP306,7"
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
        self["pickit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / self.pic_image,
            "33FJ16GS402",
        )
#        ard = self.devices["ard"]
#        self["pgmbp35sr"] = sensor.Keyed(ard, "PGM_BP35SR")
        # Console sensors
        bp35 = self.devices["bp35"]
        bp35tunnel = self.devices["bp35tunnel"]
        for name, cmdkey, units in (
            ("arm_acv", "AC_V", "Vac"),
            ("arm_acf", "AC_F", "Hz"),
            ("arm_sect", "SEC_T", "°C"),
            ("arm_vout", "BUS_V", "V"),
            ("arm_fan", "FAN", "%"),
            ("arm_canbind", "CAN_BIND", ""),
            ("arm_vbat", "BATT_V", "V"),
            ("arm_ibat", "BATT_I", "A"),
            ("arm_ibus", "BUS_I", "A"),
            ("arm_vaux", "AUX_V", "V"),
            ("arm_iaux", "AUX_I", "A"),
            ("arm_vout_ov", "VOUT_OV", ""),
            ("arm_iout", "SR_IOUT", "A"),
            ("arm_remote", "BATT_SWITCH", ""),
            # SR Solar Regulator
            ("arm_sr_alive", "SR_ALIVE", "0/1"),
            ("arm_sr_relay", "SR_RELAY", "0/1"),
            ("arm_sr_error", "SR_ERROR", ""),
            ("arm_sr_vin", "SR_VIN", "V"),
            # PM Solar Regulator
            ("arm_pm_alive", "PM_ALIVE", "0/1"),
            ("arm_pm_iout", "PM_IOUT", "A"),
            ("arm_pm_iout_rev", "PM_IOUT_REV", "-A"),
        ):
            self[name] = sensor.Keyed(bp35, cmdkey)
            if units:
                self[name].units = units
        self["arm_swver"] = sensor.Keyed(bp35, "SW_VER")
        self["TunnelSwVer"] = sensor.Keyed(bp35tunnel, "SW_VER")
        # Generate load current sensors
        loads = []
        for i in range(1, self.outputs + 1):
            loads.append(sensor.Keyed(bp35, "LOAD_{0}".format(i)))
        self["arm_loads"] = loads
        # Pre-adjust OCP
        low, high = self.limits["OCP_pre"].limit
        self["ocp_pre"] = sensor.Ramp(
            stimulus=self.devices["dcl_bat"],
            sensor=self["vbat"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(
                start=low - self.iload - 1, stop=high - self.iload + 1, step=0.1
            ),
        )
        self["ocp_pre"].units = "A"
        self["ocp_pre"].on_read = lambda value: value + self.iload
        # Post-adjust OCP
        low, high = self.limits["OCP"].limit
        self["ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_bat"],
            sensor=self["vbat"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(
                start=low - self.iload - 1, stop=high - self.iload + 1, step=0.1
            ),
        )
        self["ocp"].units = "A"
        self["ocp"].on_read = lambda value: value + self.iload


class Measurements(share.Measurements):
    """Measurements."""

    is_pm = None

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("hardware8", "HwVer8", "hardware", "Hardware version"),
                ("dmm_lock", "FixtureLock", "lock", "Fixture lid closed"),
                ("dmm_acin", "ACin", "acin", "AC input voltage"),
                ("dmm_vpfc", "Vpfc", "vpfc", "PFC output voltage"),
                ("dmm_pri12v", "12Vpri", "pri12v", "Primary 12V control rail"),
                ("dmm_15vs", "15Vs", "o15vs", "Secondary 15V rail"),
                ("dmm_vload", "Vload", "vload", "Outputs on"),
                ("dmm_vloadoff", "VloadOff", "vload", "Outputs off"),
                ("dmm_vbatin", "VbatIn", "vbat", "Injected Vbatt voltage"),
                ("dmm_vbat", "Vbat", "vbat", "Vbatt output voltage"),
                ("dmm_vaux", "Vaux", "vbat", "Vaux output voltage"),
                ("dmm_3v3", "3V3", "o3v3", "3V3 rail voltage"),
                ("dmm_fanon", "FanOn", "fan", "Fans running"),
                ("dmm_fanoff", "FanOff", "fan", "Fans off"),
                ("ramp_ocp_pre", "OCP_pre", "ocp_pre", "OCP point (pre-cal)"),
                ("ramp_ocp", "OCP", "ocp", "OCP point (post-cal)"),
                ("ui_yesnored", "Notify", "yesnored", "LED Red"),
                ("ui_yesnogreen", "Notify", "yesnogreen", "LED Green"),
                ("arm_swver", "ARM-SwVer", "arm_swver", "Unit software version"),
                ("arm_acv", "ARM-AcV", "arm_acv", "AC voltage"),
                ("arm_acf", "ARM-AcF", "arm_acf", "AC frequency"),
                ("arm_sect", "ARM-SecT", "arm_sect", "Temperature"),
                ("arm_vout", "ARM-Vout", "arm_vout", "Vbatt"),
                ("arm_fan", "ARM-Fan", "arm_fan", "FAN speed setting"),
                ("dmm_canpwr", "CanPwr", "canpwr", "CAN bus rail voltage"),
                ("arm_can_bind", "CAN_BIND", "arm_canbind", "CAN bound"),
                ("arm_vbat", "Vbat", "arm_vbat", "Battery voltage"),
                ("arm_ibat", "ARM-BattI", "arm_ibat", "Battery current"),
                ("arm_ibus", "ARM-BusI", "arm_ibus", "Bus current"),
                ("arm_vaux", "ARM-AuxV", "arm_vaux", "Aux voltage"),
                ("arm_iaux", "ARM-AuxI", "arm_iaux", "Aux current"),
                ("arm_vout_ov", "Vout_OV", "arm_vout_ov", "Vout OVP"),
                ("arm_remote", "ARM-RemoteClosed", "arm_remote", "Remote input"),
                ("TunnelSwVer", "ARM-SwVer", "TunnelSwVer", ""),
#                ("pgm_bp35sr", "Reply", "pgmbp35sr", ""),
                ("program_pic", "ProgramOk", "pickit", ""),
            )
        )
        if self.is_pm:  # PM Solar Regulator
            self.create_from_names(
                (
                    ("arm_pm_alive", "PM-Alive", "arm_pm_alive", "Solar alive"),
                    (
                        "arm_pm_iz_pre",
                        "ARM-PmSolarIz-Pre",
                        "arm_pm_iout",
                        "Solar zero current (pre-cal)",
                    ),
                    (
                        "arm_pm_iz_post",
                        "ARM-PmSolarIz-Post",
                        "arm_pm_iout",
                        "Solar zero current (post-cal)",
                    ),
                )
            )
        else:  # SR Solar Regulator
            self.create_from_names(
                (
                    ("dmm_solarvcc", "SolarVcc", "solarvcc", "Solar Vcc rrunning"),
                    ("dmm_solarvin", "SolarVin", "solarvin", "Solar input present"),
                    ("arm_sr_alive", "SR-Alive", "arm_sr_alive", "Solar alive"),
                    ("arm_sr_relay", "SR-Relay", "arm_sr_relay", "Solar relay on"),
                    (
                        "arm_sr_error",
                        "SR-Error",
                        "arm_sr_error",
                        "Solar error flag clear",
                    ),
                    (
                        "arm_sr_vin_pre",
                        "ARM-SolarVin-Pre",
                        "arm_sr_vin",
                        "Solar input voltage (pre-cal)",
                    ),
                    (
                        "arm_sr_vin_post",
                        "ARM-SolarVin-Post",
                        "arm_sr_vin",
                        "Solar input voltage (post-cal)",
                    ),
                    (
                        "dmm_vsetpre",
                        "VsetPre",
                        "vset",
                        "Solar output voltage (pre-cal)",
                    ),
                    (
                        "dmm_vsetpost",
                        "VsetPost",
                        "vset",
                        "Solar output voltage (post-cal)",
                    ),
                    (
                        "arm_ioutpre",
                        "ARM-IoutPre",
                        "arm_iout",
                        "Solar output current (pre-cal)",
                    ),
                    (
                        "arm_ioutpost",
                        "ARM-IoutPost",
                        "arm_iout",
                        "Solar output current (post-cal)",
                    ),
                )
            )
        # Generate load current measurements
        loads = []
        for sen in self.sensors["arm_loads"]:
            loads.append(tester.Measurement(self.limits["ARM-LoadI"], sen))
        self["arm_loads"] = loads
