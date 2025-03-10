#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101, RVMN300x, RVMN301x, RVMN5x and RVMN7x Initial Test Program."""

import pathlib
import time

import serial
import tester

import share
from . import console, config


class Initial(share.TestSequence):
    """RVMN101, RVMN300x, RVMN301x, RVMN5x and RVMN7x Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, self.uuts[0])
        Devices.reversed_outputs = self.cfg.values.reversed_outputs
        Sensors.nordic_devicetype = self.cfg.values.nordic_devicetype
        Sensors.nordic_image = self.cfg.values.nordic_image
        Sensors.arm_devicetype = self.cfg.values.arm_devicetype
        Sensors.arm_image = self.cfg.values.arm_image
        self.configure(self.cfg.limits_initial(), Devices, Sensors, Measurements)
        self.ble_rssi_dev()
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise),
            tester.TestStep("Input", self._step_input),
            tester.TestStep("Output", self._step_output),
            tester.TestStep("CanBus", self._step_canbus),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input power and measure voltages."""
        dev["dcs_vbatt"].output(self.cfg.vbatt_set, output=True)
        self.measure(
            (
                "dmm_vbatt",
                "dmm_3v3",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program both devices."""
        mes["JLinkARM"]()
        with dev["swd_select"]:
            mes["JLinkBLE"]()

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the unit."""
        uut = self.uuts[0]
        dev["BLE"].uut = uut
        sernum = uut.sernum
        rvmn = dev["rvmn"]
        rvmn.open()
        rvmn.reset()
        time.sleep(self.cfg.values.boot_delay)
        rvmn.brand(sernum, self.cfg.values.product_rev, self.cfg.values.hardware_rev)
        # FIXME: Power cycle module to reload everything from NV storage
        #        Check that firmware has really saved the branding data
        with tester.PathName("Verify"):
            dcs = dev["dcs_vbatt"]
            dcs.output(0.0, delay=0.5)
            dcs.output(self.cfg.vbatt_set, delay=2)
            for name, value in (  # Set the test limits
                ("Serial", sernum),
                ("ProdRev", self.cfg.values.product_rev),
                ("HardRev", self.cfg.values.hardware_rev),
            ):
                mes[name].testlimit[0].adjust("^{0}$".format(value))

# PC-RVMN101C-361 Hardware Rev not saved
#            self.measure(("Serial", "ProdRev", "HardRev"))
            # Adding time delay due to RVMN301C not getting enough time to read from serial
            time.sleep(2)
            self.measure(("Serial", "ProdRev"))

        # Save SerialNumber & MAC on a remote server.
        mac = share.MAC.loads(mes["ble_mac"]().value1)
        dev["BLE"].mac = mac.dumps(separator="")

    @share.teststep
    def _step_input(self, dev, mes):
        """Test the inputs of the unit."""
        with tester.PathName("Digital"):
            mes["dig_in"]()
        for name in mes.analog_inputs:
            with tester.PathName(name):
                mes[name]()

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the outputs of the unit."""
        rvmn = dev["rvmn"]
        if self.parameter == "200A":  # Test for 2 x wire links
            dev["rla_link"].set_on()
        if self.parameter in ("101A", "200A", "300A", "300C", "301C"): 
            rvmn.hs_output(41, False)  # Baggage Comp. Light defaults to on, so we turn it off.
        # Reversed HBridge outputs are only on 101A Rev 7-9
        if rvmn.reversed_outputs:
            # Turn LOW, then HIGH, reversed HBridge outputs in turn
            with dev["rla_pullup"]:
                for idx in rvmn.reversed_outputs:
                    with tester.PathName("REV{0}".format(idx)):
                        rvmn.hs_output(idx, True)
                        mes["dmm_hb_on"](timeout=1)
                        rvmn.hs_output(idx, False)
                        mes["dmm_hb_off"](timeout=1)
        mes["dmm_hs_off"](timeout=1)
        # Measurements from here on do not fail the test instantly.
        # Always measure all the outputs, and force a fail if any output
        # has failed. So we get a full dataset on every test.
        with share.MultiMeasurementSummary(default_timeout=2) as checker:
            # Turn ON, then OFF, each HS output in turn
            for idx in rvmn.hs_outputs:
                with tester.PathName(rvmn.output_pin_name(idx)):
                    rvmn.hs_output(idx, True)
                    checker.measure(mes["dmm_hs_on"])
                    rvmn.hs_output(idx, False)
                    checker.measure(mes["dmm_hs_off"])
            # Turn ON, then OFF, each LS output in turn
            ls_count = 1
            for idx in rvmn.ls_outputs:
                with tester.PathName(rvmn.output_pin_name(idx)):
                    dmm_channel = "dmm_ls{0}".format(ls_count)
                    rvmn.ls_output(idx, True)
                    checker.measure(mes[dmm_channel + "_on"])
                    rvmn.ls_output(idx, False)
                    checker.measure(mes[dmm_channel + "_off"])
                    ls_count += 1

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        with dev["canreader"]:
            mes["can_active"]()


class Devices(share.Devices):
    """Devices."""

    reversed_outputs = None  # Outputs with reversed operation

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_vbatt", tester.DCSource, "DCS1"),
            ("swd_select", tester.Relay, "RLA1"),
            ("rla_pullup", tester.Relay, "RLA2"),
            ("rla_link", tester.Relay, "RLA3"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console
        nordic_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        nordic_ser.port = self.port("NORDIC")
        # Console driver
        console_class = {
            "101A": console.Console101A,
            "101B": console.Console101B,
            "101C": console.Console101C,
            "200A": console.Console200A,
            "300A": console.Console300A,
            "300C": console.Console300C,
            "301C": console.Console301C,
            "50": console.Console50,
            "55": console.Console55,
            "60": console.Console60,
            "65": console.Console65,
            "70": console.Console70,
            "75": console.Console75,
        }[self.parameter]
        self["rvmn"] = console_class(nordic_ser)
        self["rvmn"].output_reversed(self.reversed_outputs)
        # CAN devices
        self["can"] = self.physical_devices["CAN"]
        self["canreader"] = tester.CANReader(self["can"])
        self["candetector"] = share.can.PacketDetector(self["canreader"])

    def run(self):
        """Test run is starting."""
        self["can"].rvc_mode = True
        self["canreader"].start()

    def reset(self):
        """Test run has stopped."""
        self["rvmn"].close()
        self["canreader"].stop()
        self["can"].rvc_mode = False
        self["dcs_vbatt"].output(0.0, False)
        for rla in ("rla_pullup", "rla_link"):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    nordic_devicetype = None
    nordic_image = None
    arm_devicetype = None
    arm_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["VBatt"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self["3V3"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self["HSout"] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.1)
        self["ReverseHB"] = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.1)
        self["LSout1"] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.1)
        self["LSout2"] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        self["JLinkBLE"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile(self.nordic_devicetype),
            pathlib.Path(__file__).parent / self.nordic_image,
        )
        self["JLinkARM"] = sensor.JLink(
            self.devices["JLink"],
            share.programmer.JFlashProject.projectfile(self.arm_devicetype),
            pathlib.Path(__file__).parent / self.arm_image,
        )
        # Console sensors
        rvmn = self.devices["rvmn"]
        self["SERIAL"] = sensor.Keyed(rvmn, "SERIAL")
        self["SERIAL"].doc = "Serial number"
        self["PRODUCT-REV"] = sensor.Keyed(rvmn, "PRODUCT-REV")
        self["PRODUCT-REV"].doc = "Product revision"
        self["HARDWARE-REV"] = sensor.Keyed(rvmn, "HARDWARE-REV")
        self["HARDWARE-REV"].doc = "Hardware revision"
        self["BleMac"] = sensor.Keyed(rvmn, "MAC")
        self["BleMac"].doc = "BLE MAC"
        # Convert "xx:xx:xx:xx:xx:xx (random)" to "xxxxxxxxxxxx"
        self["BleMac"].on_read = lambda value: value.replace(":", "").replace(
            " (random)", ""
        )
        self["Input"] = sensor.Keyed(rvmn, "INPUT")
        self["Input"].doc = "All digital inputs"
        for analog in (
            "TANK 1",
            "TANK 2",
            "TANK 3",
            "TANK 4",
            "TANK 5",
            "TANK 6",
            "VOLTAGE 1",
            "VOLTAGE 2",
            "TEMP SENSOR 1",
            "TEMP SENSOR 2",
            "TEMP SENSOR 3",
            "TEMP SENSOR 4",
            "FUEL SENSOR 1",
            "FUEL SENSOR 2",
            "VOLTAGE SYS",
        ):
            self[analog] = sensor.Keyed(rvmn, analog)
        self["cantraffic"] = sensor.Keyed(self.devices["candetector"], None)


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_3v3", "3V3", "3V3", "Micro power ok"),
                ("dmm_vbatt", "Vbatt", "VBatt", "Battery input ok"),
                ("dmm_hs_on", "HSon", "HSout", "High-side driver ON"),
                ("dmm_hs_off", "HSoff", "HSout", "All high-side drivers OFF"),
                ("dmm_hb_on", "HBon", "ReverseHB", "Test reversed HBridge 1-3 ON"),
                ("dmm_hb_off", "HBoff", "ReverseHB", "Test reversed HBridge 1-3 OFF"),
                ("dmm_ls1_on", "LSon", "LSout1", "Low-side driver1 ON"),
                ("dmm_ls1_off", "LSoff", "LSout1", "Low-side driver1 OFF"),
                ("dmm_ls2_on", "LSon", "LSout2", "Low-side driver2 ON"),
                ("dmm_ls2_off", "LSoff", "LSout2", "Low-side driver2 OFF"),
                ("can_active", "CANok", "cantraffic", "CAN traffic seen"),
                ("ble_mac", "BleMac", "BleMac", "MAC address"),
                ("JLinkARM", "ProgramOk", "JLinkARM", "Programmed"),
                ("JLinkBLE", "ProgramOk", "JLinkBLE", "Programmed"),
                ("dig_in", "AllInputs", "Input", "Digital input reading"),
                ("Serial", "Serial", "SERIAL", "Serial number saved"),
                ("ProdRev", "ProdRev", "PRODUCT-REV", "Product revision saved"),
                ("HardRev", "HardRev", "HARDWARE-REV", "Hardware revision saved"),
            )
        )
        self.analog_inputs = []
        console = self.sensors.devices["rvmn"]
        lim = self.limits["AllInputs"]
        for idx in console.analog_inputs:
            name = console.analog_pin_name(idx)
            self[name] = tester.Measurement(lim, self.sensors[name])
            self.analog_inputs.append(name)
