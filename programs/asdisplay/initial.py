#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ASDisplay Test Program."""

import pathlib

import libtester
import serial
import tester

import share
from . import console


class Initial(share.TestSequence):
    """ASDisplay Initial Test Program."""

    vin_set = 12.0  # Input voltage (V)
    sw_arm_image = "ASDisplay 1.2.0.bin"  # PC-30654
    limitdata = (
        libtester.LimitDelta("Vin", vin_set, 0.5, doc="At nominal"),
        libtester.LimitPercent("3V3", 3.33, 3.0, doc="At nominal"),
        libtester.LimitPercent("5V", 5.0, 3.0, doc="At nominal"),
        libtester.LimitRegExp("test_mode", "^OK$"),
        libtester.LimitRegExp("leds_on", "^OK$"),
        libtester.LimitRegExp("leds_off", "^OK$"),
        libtester.LimitInteger("TankLevel0", 0),
        libtester.LimitInteger("TankLevel1", 1),
        libtester.LimitInteger("TankLevel2", 2),
        libtester.LimitInteger("TankLevel3", 3),
        libtester.LimitInteger("TankLevel4", 4),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
    )
    # In testmode, updates of the water tank levels are less than 100ms.
    analog_read_wait = 0.1  # Analog read response time

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.sw_arm_image = self.sw_arm_image
        super().configure(self.limitdata, Devices, Sensors, Measurements)
        super().open(uut)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("PgmARM", self.devices["programmer"].program),
            tester.TestStep("Testmode", self._step_enter_testmode),
            tester.TestStep("LEDCheck", self._step_led_check),
            tester.TestStep("TankSense", self._step_tank_sense),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply Vin and check voltages."""
        dev["dcs_vin"].output(self.vin_set, output=True, delay=1)
        self.measure(
            (
                "dmm_Vin",
                "dmm_5V",
                "dmm_3V3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_enter_testmode(self, dev, mes):
        con = dev["console"]
        con.open()
        con.reset()
        mes["test_mode"]()

    @share.teststep
    def _step_led_check(self, dev, mes):
        """Toggle LED's."""
        self.measure(
            (
                "LEDsOn",
                "LED_check",
                "LEDsOff",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Tank sensors."""
        for num in range(5):  # 0 to 4 relays activated
            if num:
                dev["relay{0}".format(num)].set_on(delay=self.analog_read_wait)
            mes["tank_level{0}".format(num)]()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        with dev["canreader"]:
            mes["can_active"]()


class Devices(share.Devices):
    """Devices."""

    sw_arm_image = None

    def open(self):
        """Create all Instruments."""
        fixture = "036746"
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vin", tester.DCSource, "DCS1"),
            ("relay1", tester.Relay, "RLA1"),
            ("relay2", tester.Relay, "RLA2"),
            ("relay3", tester.Relay, "RLA3"),
            ("relay4", tester.Relay, "RLA4"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.config.Fixture.port(fixture, "ARM")
        self["programmer"] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_arm_image,
            crpmode=False,
            bda4_signals=True,  # Use BDA4 serial lines for RESET & BOOT
        )
        # Serial connection to the console
        console_ser = serial.Serial()
        # Set port separately, as we don't want it opened yet
        console_ser.port = arm_port
        self["console"] = console.Console(console_ser)
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
        self["dcs_vin"].output(0.0, output=False)
        for rla in ("relay1", "relay2", "relay3", "relay4"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["Vin"] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.01)
        self["Vin"].doc = "Vin rail"
        self["3V3"] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.01)
        self["3V3"].doc = "3V3 rail"
        self["5V"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["5V"].doc = "5V rail"
        self["LEDsOnCheck"] = sensor.YesNo(
            message=tester.translate("asdisplay_initial", "AreLedsOn?"),
            caption=tester.translate("asdisplay_initial", "capLedCheck"),
        )
        self["LEDsOnCheck"].doc = "LEDs Turned on"
        # Console sensors
        console = self.devices["console"]
        self["tank_sensor"] = sensor.Keyed(console, "TANK_LEVEL")
        for name, cmdkey in (
            ("test_mode", "TESTMODE"),
            ("leds_on", "ALL_LEDS_ON"),
            ("leds_off", "LEDS_OFF"),
        ):
            self[name] = sensor.Keyed(console, cmdkey)
        self["cantraffic"] = sensor.Keyed(self.devices["candetector"], None)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                # measurement_name, limit_name, sensor_name, doc
                ("dmm_Vin", "Vin", "Vin", "Vin rail ok"),
                ("dmm_3V3", "3V3", "3V3", "3V3 rail ok"),
                ("dmm_5V", "5V", "5V", "5V rail ok"),
                ("test_mode", "test_mode", "test_mode", "Test Mode Entered"),
                ("LED_check", "Notify", "LEDsOnCheck", "LED check ok"),
                ("LEDsOn", "leds_on", "leds_on", "LEDs On"),
                ("LEDsOff", "leds_off", "leds_off", "LEDs Off"),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
            )
        )
        self["tank_level0"] = tester.Measurement(
            (self.limits["TankLevel0"],) * 4,  # A tuple of limits
            self.sensors["tank_sensor"],
            doc="No inputs active",
        )
        self["tank_level1"] = tester.Measurement(
            (self.limits["TankLevel1"],) * 4,
            self.sensors["tank_sensor"],
            doc="1 input active",
        )
        self["tank_level2"] = tester.Measurement(
            (self.limits["TankLevel2"],) * 4,
            self.sensors["tank_sensor"],
            doc="2 inputs active",
        )
        self["tank_level3"] = tester.Measurement(
            (self.limits["TankLevel3"],) * 4,
            self.sensors["tank_sensor"],
            doc="3 inputs active",
        )
        self["tank_level4"] = tester.Measurement(
            (self.limits["TankLevel4"],) * 4,
            self.sensors["tank_sensor"],
            doc="4 inputs active",
        )
