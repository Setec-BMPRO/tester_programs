#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Final Test Program."""

import serial
import tester

import share
from . import config, device, arduino


class Final(share.TestSequence):

    """RVSWT101 Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter, uut)
        button_count = self.cfg["button_count"]
        Devices.fixture_num = self.cfg["fixture_num"]
        Devices.button_count = button_count
        limits_fin = {
            4: "limits_fin_4_button",
            6: "limits_fin_6_button",
        }[button_count]
        super().open(self.cfg[limits_fin], Devices, Sensors, Measurements)
        self.steps = (tester.TestStep("Bluetooth", self._step_bluetooth),)
        self.sernum = None
        self.buttons = []  # 12 or 18 measurement name strings
        buttons_in_use = range(1, button_count + 1)
        button_presses = ["buttonPress_{0}".format(button) for button in buttons_in_use]
        button_measurements = [
            "buttonMeasure_{0}".format(button) for button in buttons_in_use
        ]
        button_releases = [
            "buttonRelease_{0}".format(button) for button in buttons_in_use
        ]
        for button_press, button_test, button_release in zip(
            button_presses, button_measurements, button_releases
        ):
            self.buttons.extend([button_press, button_test, button_release])
        # Do RSSI measurement when button 1 is held down
        self.buttons.insert(1, "rssi")

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_serialnum")
        dev["ble"].uut = self.uuts[0]
        # Measure the MAC to save it in test result data
        mac = dev["ble"].mac
        mes["ble_mac"].sensor.store(mac)
        mes["ble_mac"]()
        if not dev["ard"].check_uut_in_place():
            mes["ui_add_uut"]()
            if not dev["ard"].check_uut_in_place():
                uut_check = tester.Measurement(
                    tester.LimitBoolean(
                        "Detect UUT is in fixture",
                        True,
                        "No UUT was detected in the fixture",
                    ),
                    tester.sensor.Mirror(),
                )
                uut_check.sensor.store(False)
                uut_check()
        # Perform button press measurements
        self.measure(self.buttons, timeout=10)
        # Don't bluetooth scan for any measurement from here on
        dev["decoder"].always_scan = False
        self.measure(
            (
                "cell_voltage",
                "switch_type",
            )
        )
        # Eject the UUT if we make it to the end of the test
        dev["ard"].eject_uut()


class Devices(share.Devices):

    """Devices."""

    fixture_num = None  # Fixture number
    button_count = None  # 4 or 6 button selection

    def open(self):
        """Create all Instruments."""
        # BLE MAC & Scanning server
        self["ble"] = tester.BLE(
            (self.physical_devices["BLE"], self.physical_devices["MAC"])
        )
        # BLE Packet decoder
        self["decoder"] = device.RVSWT101(self["ble"])
        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=20.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port(self.fixture_num, "ARDUINO")
        self["ard"] = arduino.Arduino(ard_ser)
        self["ard"].open()
        self.add_closer(lambda: self["ard"].close())
        self["ard"].retract_all()
        self["ard"].exercise_actuators()
        self["ard"].set_state(self.button_count)

    def reset(self):
        """Reset instruments."""
        self["decoder"].reset()
        self["ard"].retract_all()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self["mirmac"] = sensor.Mirror()
        self["SnEntry"] = sensor.DataEntry(
            message=tester.translate("rvswt101_final", "msgSnEntry"),
            caption=tester.translate("rvswt101_final", "capSnEntry"),
        )
        self["ButtonPress"] = sensor.OkCan(
            message=tester.translate("rvswt101_final", "msgPressButton"),
            caption=tester.translate("rvswt101_final", "capPressButton"),
        )
        self["AddUUT"] = sensor.OkCan(
            message=tester.translate("rvswt101_final", "msgAddUUT"),
            caption=tester.translate("rvswt101_final", "capAddUUT"),
        )
        decoder = self.devices["decoder"]  # tester.BLE device
        self["cell_voltage"] = sensor.Keyed(decoder, "cell_voltage")
        self["switch_type"] = sensor.Keyed(decoder, "switch_type")
        self["RSSI"] = sensor.Keyed(decoder, "rssi")
        self["RSSI"].rereadable = True
        for button in range(1, 7):
            name = "switch_{0}_measure".format(button)
            self[name] = sensor.Keyed(decoder, "switch_code")
            self[name].rereadable = True
        # Arduino sensors - sensor_name, key
        ard = self.devices["ard"]
        for name, cmdkey in (
            ("debugOn", "DEBUG"),
            ("debugOff", "QUIET"),
            ("retractAll", "RETRACT_ACTUATORS"),
            ("ejectDut", "EJECT_DUT"),
            ("4ButtonModel", "4BUTTON_MODEL"),
            ("6ButtonModel", "6BUTTON_MODEL"),
            ("exercise_actuators", "EXERCISE"),
        ):
            self[name] = sensor.Keyed(ard, cmdkey)
        # Create additional arduino sensors for buttonPress and buttonRelease
        for button in range(1, 7):
            _data = (
                ("buttonPress_{0}".format(button), "PRESS_BUTTON_{0}".format(button)),
                (
                    "buttonRelease_{0}".format(button),
                    "RELEASE_BUTTON_{0}".format(button),
                ),
            )
            for name, cmdkey in _data:
                self[name] = sensor.Keyed(ard, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements.
        measurement_name, limit_name, sensor_name, doc"""

        self.create_from_names(
            (
                ("ui_serialnum", "SerNum", "SnEntry", ""),
                ("ble_mac", "BleMac", "mirmac", "Get MAC address from server"),
                ("ui_add_uut", "ButtonOk", "AddUUT", ""),
                ("debugOn", "Reply", "debugOn", ""),
                ("debugOff", "Reply", "debugOff", ""),
                ("buttonPress_1", "Reply", "buttonPress_1", ""),
                ("buttonPress_2", "Reply", "buttonPress_2", ""),
                ("buttonPress_3", "Reply", "buttonPress_3", ""),
                ("buttonPress_4", "Reply", "buttonPress_4", ""),
                ("buttonPress_5", "Reply", "buttonPress_5", ""),
                ("buttonPress_6", "Reply", "buttonPress_6", ""),
                ("buttonRelease_1", "Reply", "buttonRelease_1", ""),
                ("buttonRelease_2", "Reply", "buttonRelease_2", ""),
                ("buttonRelease_3", "Reply", "buttonRelease_3", ""),
                ("buttonRelease_4", "Reply", "buttonRelease_4", ""),
                ("buttonRelease_5", "Reply", "buttonRelease_5", ""),
                ("buttonRelease_6", "Reply", "buttonRelease_6", ""),
                ("retractAll", "Reply", "retractAll", ""),
                ("ejectDut", "Reply", "ejectDut", ""),
                ("4ButtonModel", "Reply", "4ButtonModel", ""),
                ("6ButtonModel", "Reply", "6ButtonModel", ""),
                ("cell_voltage", "CellVoltage", "cell_voltage", "Button cell charged"),
                ("switch_type", "SwitchType", "switch_type", "Switch type"),
                ("rssi", "RSSI Level", "RSSI", "Bluetooth RSSI Level"),
                (
                    "buttonMeasure_1",
                    "switch_1_pressed",
                    "switch_1_measure",
                    "Button 1 tested",
                ),
                (
                    "buttonMeasure_2",
                    "switch_2_pressed",
                    "switch_2_measure",
                    "Button 2 tested",
                ),
                (
                    "buttonMeasure_3",
                    "switch_3_pressed",
                    "switch_3_measure",
                    "Button 3 tested",
                ),
                (
                    "buttonMeasure_4",
                    "switch_4_pressed",
                    "switch_4_measure",
                    "Button 4 tested",
                ),
                (
                    "buttonMeasure_5",
                    "switch_5_pressed",
                    "switch_5_measure",
                    "Button 5 tested",
                ),
                (
                    "buttonMeasure_6",
                    "switch_6_pressed",
                    "switch_6_measure",
                    "Button 6 tested",
                ),
                ("exercise_actuators", "Reply", "exercise_actuators", ""),
            )
        )
        # Suppress signals on these measurements.
        for name in (
            "buttonRelease_1",
            "buttonRelease_2",
            "buttonRelease_3",
            "buttonRelease_4",
            "buttonRelease_5",
            "buttonRelease_6",
            "retractAll",
            "debugOn",
            "debugOff",
            "retractAll",
            "ejectDut",
            "4ButtonModel",
            "6ButtonModel",
        ):
            self[name].send_signal = False
