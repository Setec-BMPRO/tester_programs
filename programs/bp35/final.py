#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""BP35 / BP35-II Final Test Program."""

import tester

import share
from . import console, config


class Final(share.TestSequence):

    """BP35 / BP35-II Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        limits = self.cfg.limits_final()
        super().open(limits, Devices, Sensors, Measurements)
        self.limits["ARM-SwVer"].adjust(
            "^{0}$".format(self.cfg.arm_sw_version.replace(".", r"\."))
        )
        self.steps = (
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("CAN", self._step_can),
            tester.TestStep("Load", self._step_load),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("CanCable", self._step_can_cable),
        )
        self.sernum = None

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit and measure output voltages."""
        self.sernum = self.get_serial(self.uuts, "SerNum", "ui_sernum")
        mes["dmm_fanoff"](timeout=5)
        dev["acsource"].output(voltage=self.cfg.vac, output=True)
        mes["dmm_fanon"](timeout=15)
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(14):
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["dmm_vouts"][load])

    @share.teststep
    def _step_can(self, dev, mes):
        """Access the unit console using the CAN bus."""
        mes["dmm_can12v"](timeout=5)
        bp35 = dev["bp35"]
        bp35.open()
        mes["arm_swver"]()
        # Set unit internal Serial Number to match the outside label
        bp35["SER_ID"] = self.sernum
        bp35["NVWRITE"] = True
        bp35.close()

    @share.teststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev["dcl_out"].output(1.0, output=True)
        dev["dcl_out"].binary(1.0, 34.0, 2.0, delay=0.2)
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(14):
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["dmm_vloads"][load])

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes["ramp_ocp"](timeout=5)

    @share.teststep
    def _step_can_cable(self, dev, mes):
        """Remove CAN cable."""
        self.measure(
            (
                "ui_notifycable",
                "dmm_can0v",
            ),
            timeout=5,
        )


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        self["dmm"] = tester.DMM(self.physical_devices["DMM"])
        self["acsource"] = tester.ACSource(self.physical_devices["ACS"])
        self["dcs_photo"] = tester.DCSource(self.physical_devices["DCS1"])
        self["dcl_out"] = tester.DCLoad(self.physical_devices["DCL1"])
        tunnel = tester.CANTunnel(
            self.physical_devices["CAN"], share.can.SETECDeviceID.BP35.value
        )
        self["bp35"] = console.TunnelConsole(tunnel)
        self["dcs_photo"].output(12.0, True)
        self.add_closer(lambda: self["dcs_photo"].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl_out"].output(15.0, delay=2)
        self["dcl_out"].output(0.0, False)
        self["bp35"].close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["photo"] = sensor.Vdc(dmm, high=15, low=2, rng=100, res=0.1)
        self["photo"].doc = "Airflow detector"
        self["can12v"] = sensor.Vdc(dmm, high=16, low=3, rng=100, res=0.1)
        self["can12v"].doc = "X303 CAN_POWER"
        bp35 = self.devices["bp35"]
        self["arm_swver"] = sensor.Keyed(bp35, "SW_VER")
        self["notifycable"] = sensor.Notify(
            message=tester.translate("bp35_final", "PullCableOut"),
            caption=tester.translate("bp35_final", "capCableOut"),
        )
        self["notifycable"].doc = "Tester operator"
        self["sernum"] = sensor.DataEntry(
            message=tester.translate("bp35_final", "msgSnEntry"),
            caption=tester.translate("bp35_final", "capSnEntry"),
        )
        self["sernum"].doc = "Barcode scanner"
        # Generate load voltage sensors
        vloads = []
        for i in range(14):
            sen = sensor.Vdc(dmm, high=i + 1, low=1, rng=100, res=0.001)
            sen.doc = "Output #{0}".format(i + 1)
            vloads.append(sen)
        self["vloads"] = vloads
        low, high = self.limits["OCP"].limit
        self["ocp"] = sensor.Ramp(
            stimulus=self.devices["dcl_out"],
            sensor=self["vloads"][0],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=low - 1, stop=high + 1, step=0.1),
            delay=0.1,
        )
        self["ocp"].doc = "OCP trip value"
        self["ocp"].units = "Adc"


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_fanoff", "FanOff", "photo", "Fan not running"),
                ("dmm_fanon", "FanOn", "photo", "Fan running"),
                ("dmm_can12v", "Can12V", "can12v", "CAN Bus 12V"),
                ("dmm_can0v", "Can0V", "can12v", "CAN Bus 0V"),
                ("ramp_ocp", "OCP", "ocp", "Output OCP"),
                ("ui_notifycable", "Notify", "notifycable", "Remove the CAN cable"),
                ("ui_sernum", "SerNum", "sernum", "Unit serial number"),
                ("arm_swver", "ARM-SwVer", "arm_swver", "Unit software version"),
            )
        )
        # Generate load measurements
        vouts = []
        vloads = []
        for sen in self.sensors["vloads"]:
            vouts.append(
                tester.Measurement(
                    self.limits["Vout"], sen, doc="No load output voltage"
                )
            )
            vloads.append(
                tester.Measurement(
                    self.limits["Vload"], sen, doc="Loaded output voltage"
                )
            )
        self["dmm_vouts"] = vouts
        self["dmm_vloads"] = vloads
