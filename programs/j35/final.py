#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""J35 Final Test Program."""

import tester
import share
from . import console
from . import config


class Final(share.TestSequence):
    """J35 Final Test Program."""

    def open(self, uut):
        """Prepare for testing."""
        self.cfg = config.get(self.parameter, uut)
        limits = self.cfg.limits_final()
        Sensors.output_count = self.cfg.output_count
        self.duplicate_limit_error = False
        super().configure(limits, Devices, Sensors, Measurements)
        super().open(uut)
        self.limits["SwVer"].adjust(
            "^{0}$".format(self.cfg.sw_version.replace(".", r"\."))
        )
        self.steps = (
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("CAN", self._step_can, self.cfg.canbus),
            tester.TestStep("Load", self._step_load),
            tester.TestStep("OCP", self._step_ocp),
            tester.TestStep("CanCable", self._step_can_cable, self.cfg.canbus),
        )

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        mes["dmm_fanoff"](timeout=5)
        dev["acsource"].output(240.0, output=True)
        mes["dmm_fanon"](timeout=15)
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(self.cfg.output_count):
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["dmm_vouts"][load])

    @share.teststep
    def _step_can(self, dev, mes):
        """Access the unit console using the CAN bus."""
        mes["dmm_can12v"](timeout=5)
        j35 = dev["j35"]
        j35.open()
        mes["swver"]()
        # Set unit internal Serial Number to match the outside label
        j35.set_sernum(self.uuts[0].sernum)
        j35.close()

    @share.teststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev["dcl_out"].output(1.0, output=True)
        dev["dcl_out"].binary(
            1.0, self.cfg.output_count * self.cfg.load_per_output, 5.0
        )
        with share.MultiMeasurementSummary(default_timeout=5) as checker:
            for load in range(self.cfg.output_count):
                with tester.PathName("L{0}".format(load + 1)):
                    checker.measure(mes["dmm_vloads"][load])

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes["ramp_ocp"](timeout=5)
        dev["acsource"].reset()

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
        for name, devtype, phydevname, doc in (
            ("dmm", tester.DMM, "DMM", "Multimeter"),
            ("acsource", tester.ACSource, "ACS", "AC input power"),
            ("dcs_photo", tester.DCSource, "DCS3", "Power to airflow detector"),
            ("dcl_out", tester.DCLoad, "DCL1", "Load shared by all outputs"),
        ):
            self[name] = devtype(self.physical_devices[phydevname], doc)
        tunnel = tester.CANTunnel(
            self.physical_devices["CAN"], share.can.SETECDeviceID.J35.value
        )
        self["j35"] = console.TunnelConsole(tunnel)
        self["dcs_photo"].output(12.0, True)
        self.add_closer(lambda: self["dcs_photo"].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self["acsource"].reset()
        self["dcl_out"].output(15.0, delay=2)
        self["dcl_out"].output(0.0, False)
        self["j35"].close()


class Sensors(share.Sensors):
    """Sensors."""

    output_count = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["photo"] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self["photo"].doc = "Airflow detector"
        self["can12v"] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.1)
        self["can12v"].doc = "X303 CAN_POWER"
        # Generate load voltage sensors
        vloads = []
        for i in range(self.output_count):
            sen = sensor.Vdc(dmm, high=i + 5, low=3, rng=100, res=0.001)
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
        j35 = self.devices["j35"]
        self["swver"] = sensor.Keyed(j35, "SW_VER")
        self["notifycable"] = sensor.Notify(
            message=tester.translate("j35_final", "PullCableOut"),
            caption=tester.translate("j35_final", "capCableOut"),
        )
        self["notifycable"].doc = "Tester operator"


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names(
            (
                ("dmm_fanoff", "FanOff", "photo", "Fan not running"),
                ("dmm_can12v", "Can12V", "can12v", "CAN Bus 12V"),
                ("dmm_can0v", "Can0V", "can12v", "CAN Bus 0V"),
                ("dmm_fanon", "FanOn", "photo", "Fan running"),
                ("ramp_ocp", "OCP", "ocp", "Output OCP"),
                ("swver", "SwVer", "swver", "Unit software version"),
                ("ui_notifycable", "Notify", "notifycable", "Remove the CAN cable"),
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
