#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd.
"""BatteryCheck Final Test Program."""

import serial

import tester

import share

from . import eunistone_pan1322


class Final(share.TestSequence):

    """BatteryCheck Final Test Program."""

    # Software binary version
    arm_version = "1.7.4080"
    limitdata = (
        tester.LimitDelta("12V", 12.0, 0.1),
        tester.LimitBoolean("BTscan", True),
        tester.LimitBoolean("BTpair", True),
        tester.LimitBoolean("ARMSerNum", True),
        tester.LimitRegExp("ARMSwVer", "^{0}$".format(arm_version.replace(".", r"\."))),
    )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("TestBlueTooth", self._step_test_bluetooth),
        )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power the battery check."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_SnEntry")
        dev["dcs_input"].output(12.0, output=True)
        mes["dmm_12V"](timeout=5)

    @share.teststep
    def _step_test_bluetooth(self, dev, mes):
        """Scan for BT devices and match against serial number."""
        blue = dev["bt"]
        blue.open()
        mac, pin = blue.scan(self.sernum)
        mes["BTscan"].sensor.store(mac is not None)
        mes["BTscan"]()
        try:
            blue.reset()
            blue.pair(mac, pin)
            _paired = True
        except eunistone_pan1322.BtRadioError:
            _paired = False
        mes["BTpair"].sensor.store(_paired)
        mes["BTpair"]()
        blue.data_mode_enter()
        info = blue.jsonrpc("GetSystemInfo")
        mes["SwVerARM"].sensor.store((info["SoftwareVersion"],))
        mes["SwVerARM"]()
        mes["SerNumARM"].sensor.store(info["SerialID"] == self.sernum)
        mes["SerNumARM"]()
        blue.data_mode_escape()
        blue.unpair()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_input", tester.DCSource, "DCS2"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the Bluetooth device
        btport = serial.Serial(baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        btport.port = share.config.Fixture.port("027013", "BT")
        # BT Radio driver
        self["bt"] = eunistone_pan1322.BtRadio(btport)

    def reset(self):
        """Reset instruments."""
        self["bt"].close()
        self["dcs_input"].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["oMirBT"] = sensor.Mirror()
        self["oMirSwVer"] = sensor.Mirror()
        self["o12V"] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self["oSnEntry"] = sensor.DataEntry(
            message=tester.translate("batterycheck_final", "msgSnEntry"),
            caption=tester.translate("batterycheck_final", "capSnEntry"),
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("BTscan", "BTscan", "oMirBT", ""),
                ("BTpair", "BTpair", "oMirBT", ""),
                ("SerNumARM", "ARMSerNum", "oMirBT", ""),
                ("SwVerARM", "ARMSwVer", "oMirSwVer", ""),
                ("dmm_12V", "12V", "o12V", ""),
                ("ui_SnEntry", "SerNum", "oSnEntry", ""),
            )
        )
