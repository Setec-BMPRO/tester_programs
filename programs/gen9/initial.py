#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""GEN9-540 Initial Test Program."""

import pathlib

import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):

    """GEN9-540 Initial Test Program."""

    pfc_stable = 0.05  # Reading to reading difference for PFC voltage stability

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config
        self.cfg.configure(uut)
        Sensors.devicetype = self.cfg.devicetype
        Sensors.sw_image = self.cfg.sw_image
        super().open(self.cfg.limits_initial, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep("PartDetect", self._step_part_detect),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("Initialise", self._step_initialise_arm),
            tester.TestStep("PowerUp", self._step_powerup),
            tester.TestStep("5V", self._step_reg_5v),
            tester.TestStep("12V", self._step_reg_12v),
            tester.TestStep("24V", self._step_reg_24v),
        )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.

        """
        self.measure(("dmm_lock", "dmm_fanshort"), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev["dcs_5v"].output(5.0, True)
        mes["dmm_3v3"](timeout=5)
        mes["JLink"]()

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Unit is left unpowered.

        """
        arm = dev["arm"]
        arm.open()
        arm.initialise()
        dev["dcs_5v"].output(0.0, False)
        dev["dcl_5v"].output(0.1, True, delay=0.5)
        dev["dcl_5v"].output(0.0, True)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev["acsource"].output(voltage=240.0, output=True)
        self.measure(
            (
                "dmm_acin",
                "dmm_15vccpri",
                "dmm_12vpri",
                "dmm_5vset",
                "dmm_12voff",
                "dmm_24voff",
                "dmm_pwrfail",
            ),
            timeout=5,
        )
        dev["rla_pson"].set_on()  # Switch all outputs ON
        self.measure(
            (
                "dmm_5vset",
                "dmm_24v",
                "dmm_12v",
            ),
            timeout=5,
        )
        arm = dev["arm"]
        arm.banner()
        arm.unlock()
        # A little load so PFC voltage falls faster
        self.dcload((("dcl_12v", 1.0), ("dcl_24v", 1.0)), output=True)
        # Calibrate the PFC set voltage
        pfc = mes["dmm_pfcpre"].stable(self.pfc_stable).value1
        arm.calpfc(pfc)
        mesres = mes["dmm_pfcpost1"].stable(self.pfc_stable)
        if not mesres.result:  # 1st retry
            arm.calpfc(mesres.value1)
            mesres = mes["dmm_pfcpost2"].stable(self.pfc_stable)
        if not mesres.result:  # 2nd retry
            arm.calpfc(mesres.value1)
            mesres = mes["dmm_pfcpost3"].stable(self.pfc_stable)
        if not mesres.result:  # 3rd retry
            arm.calpfc(mesres.value1)
            mes["dmm_pfcpost4"].stable(self.pfc_stable)
        arm.nvwrite()
        # A final PFC setup check
        mes["dmm_pfcpost"].stable(self.pfc_stable)
        self.measure(
            (
                "arm_acfreq",
                "arm_acvolt",
                "arm_5v",
                "arm_12v",
                "arm_24v",
            ),
        )

    @share.teststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Unit is left running at no load.

        """
        self.dcload(
            (
                ("dcl_12v", 1.0),
                ("dcl_24v", 0.1),
            )
        )
        self.reg_check(
            dmm_out=mes["dmm_5v"], dcl_out=dev["dcl_5v"], max_load=2.0, peak_load=2.5
        )

    @share.teststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 1.0, Max = 24A, Peak = 26A
        Unit is left running at no load.

        """
        dev["dcl_24v"].output(0.1)
        self.reg_check(
            dmm_out=mes["dmm_12v"],
            dcl_out=dev["dcl_12v"],
            max_load=24.0,
            peak_load=26.0,
        )

    @share.teststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 10A, Peak = 11A
        Unit is left running at no load.

        """
        dev["dcl_12v"].output(1.0)
        self.reg_check(
            dmm_out=mes["dmm_24v"],
            dcl_out=dev["dcl_24v"],
            max_load=10.0,
            peak_load=11.0,
        )

    def reg_check(self, dmm_out, dcl_out, max_load, peak_load):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        max_load: Maximum output load.
        peak_load: Peak output load.
        fet: Measurement instance to check 24V output FET

        Unit is left running at no load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName("NoLoad"):
            dcl_out.output(0.0)
            dcl_out.opc()
            dmm_out.measure()
        with tester.PathName("MaxLoad"):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
        with tester.PathName("PeakLoad"):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()
        self.dcload(
            (
                ("dcl_5v", 0.0),
                ("dcl_12v", 0.0),
                ("dcl_24v", 0.0),
            )
        )


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_5v", tester.DCSource, "DCS2"),
            ("dcl_24v", tester.DCLoad, "DCL3"),
            ("dcl_12a", tester.DCLoad, "DCL2"),
            ("dcl_12b", tester.DCLoad, "DCL6"),
            ("dcl_5v", tester.DCLoad, "DCL4"),
            ("rla_pson", tester.Relay, "RLA1"),
            ("JLink", tester.JLink, "JLINK"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcl_12v"] = tester.DCLoadParallel(
            ((self["dcl_12a"], 10), (self["dcl_12b"], 10))
        )
        # Serial uses a BDA4 with DTR driving RESET
        arm_ser = serial.Serial(baudrate=115200, timeout=2)
        # Set port separately - don't open until after programming
        arm_ser.port = share.config.Fixture.port("032715", "ARM")
        self["arm"] = console.Console(arm_ser)

    def reset(self):
        """Reset instruments."""
        self["arm"].close()
        # Switch off AC Source and discharge the unit
        self["acsource"].reset()
        self["dcl_5v"].output(1.0)
        self["dcl_12v"].output(5.0)
        self["dcl_24v"].output(5.0, delay=0.5)
        self["discharge"].pulse()
        for ld in ("dcl_5v", "dcl_12v", "dcl_24v"):
            self[ld].output(0.0, False)
        self["dcs_5v"].output(0.0, False)
        self["rla_pson"].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    devicetype = None
    sw_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["acin"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["pfc"] = sensor.Vdc(dmm, high=3, low=3, rng=1000, res=0.001)
        self["o15vccpri"] = sensor.Vdc(dmm, high=16, low=3, rng=100, res=0.01)
        self["o12vpri"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self["o3v3"] = sensor.Vdc(dmm, high=5, low=4, rng=10, res=0.001)
        self["o5v"] = sensor.Vdc(dmm, high=6, low=4, rng=10, res=0.001)
        self["o12v"] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self["o24v"] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self["pwrfail"] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.01)
        self["fanshort"] = sensor.Res(dmm, high=10, low=5, rng=1000, res=0.1)
        self["lock"] = sensor.Res(dmm, high=11, low=6, rng=10000, res=1)
        arm = self.devices["arm"]
        for name, cmdkey in (
            ("arm_acfreq", "AcFreq"),
            ("arm_acvolt", "AcVolt"),
            ("arm_5v", "5V"),
            ("arm_12v", "12V"),
            ("arm_24v", "24V"),
        ):
            self[name] = sensor.Keyed(arm, cmdkey)
        for name, cmdkey in (
            ("arm_swver", "SwVer"),
            ("arm_swbld", "SwBld"),
        ):
            self[name] = sensor.Keyed(arm, cmdkey)
        self["JLink"] = sensor.JLink(
            self.devices["JLink"],
            share.config.JFlashProject(self.devicetype),
            pathlib.Path(__file__).parent / self.sw_image,
        )


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", ""),
                ("dmm_fanshort", "FanShort", "fanshort", ""),
                ("dmm_acin", "ACin", "acin", ""),
                ("dmm_15vccpri", "15Vccpri", "o15vccpri", ""),
                ("dmm_12vpri", "12Vpri", "o12vpri", ""),
                ("dmm_3v3", "3V3", "o3v3", ""),
                ("dmm_5vset", "5Vset", "o5v", ""),
                ("dmm_5v", "5V", "o5v", ""),
                ("dmm_12voff", "12Voff", "o12v", ""),
                ("dmm_12v", "12V", "o12v", ""),
                ("dmm_24voff", "24Voff", "o24v", ""),
                ("dmm_24v", "24V", "o24v", ""),
                ("dmm_pfcpre", "PFCpre", "pfc", ""),
                ("dmm_pfcpost1", "PFCpost1", "pfc", ""),
                ("dmm_pfcpost2", "PFCpost2", "pfc", ""),
                ("dmm_pfcpost3", "PFCpost3", "pfc", ""),
                ("dmm_pfcpost4", "PFCpost4", "pfc", ""),
                ("dmm_pfcpost", "PFCpost", "pfc", ""),
                ("dmm_pwrfail", "PwrFail", "pwrfail", ""),
                ("arm_acfreq", "ARM-AcFreq", "arm_acfreq", ""),
                ("arm_acvolt", "ARM-AcVolt", "arm_acvolt", ""),
                ("arm_5v", "ARM-5V", "arm_5v", ""),
                ("arm_12v", "ARM-12V", "arm_12v", ""),
                ("arm_24v", "ARM-24V", "arm_24v", ""),
                ("JLink", "ProgramOk", "JLink", "Programmed"),
            )
        )
        # Prevent test failures on these limits.
        for name in (
            "dmm_pfcpost1",
            "dmm_pfcpost2",
            "dmm_pfcpost3",
            "dmm_pfcpost4",
        ):
            self[name].position_fail = False
