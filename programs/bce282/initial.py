#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BCE282-12/24 Initial Test Program."""

import os
import pathlib
import sys
import time

import libtester
import serial
import tester

import share
from . import console
from . import tosbsl


class Initial(share.TestSequence):
    """BCE282-12/24 Initial Test Program."""

    # Calibration data save file (TI Text format)
    msp_savefile = pathlib.Path(
        {  # Must be writable by the tester login
            "posix": "/home/setec/testdata/bslsavedata.txt",
            "nt": "C:/TestGear/TestData/bslsavedata.txt",
        }[os.name]
    )
    # Password data save file
    msp_password = pathlib.Path(
        {  # Must be writable by the tester login
            "posix": "/home/setec/testdata/bslpassword.txt",
            "nt": "C:/TestGear/TestData/bslpassword.txt",
        }[os.name]
    )
    # TI Text format firmware image
    _hexfile = "bce282_4a.txt"
    # Factor to tighten the calibration check
    _cal_factor = 0.5
    # Injected Vcc Bias
    _vcc_bias_set = 15.0
    # Limits common to both versions
    _common = (
        libtester.LimitLow("FixtureLock", 200),
        libtester.LimitDelta("VccBiasExt", _vcc_bias_set, 1.0),
        libtester.LimitDelta("Vac", 240.0, 5.0),
        libtester.LimitBetween("Vbus", 330.0, 350.0),
        libtester.LimitPercent("VccPri", 15.6, 5.0),
        libtester.LimitPercent("VccBias", 15.0, 13.0),
        libtester.LimitLow("VbatOff", 0.5),
        libtester.LimitBetween("AlarmClosed", 1000, 3000),
        libtester.LimitBetween("AlarmOpen", 11000, 13000),
        libtester.LimitBetween("Status 0", -0.1, 0.1),
    )
    # ScaleFactor: 24V model responds with 12V output to measurement "msp_vout"
    # and is designed to be calibrated with half its measured output voltage.
    limitdata = {  # Test limit selection keyed by program parameter
        "12": {
            "Limits": _common
            + (
                libtester.LimitBetween("OutOCP", 20.05, 24.00),
                libtester.LimitBetween("BattOCP", 14.175, 15.825),
                libtester.LimitLow("InOCP", 13.0),
                libtester.LimitPercent("VoutPreCal", 13.8, 2.6),
                libtester.LimitDelta("VoutPostCal", 13.8, _cal_factor * 0.15),
                libtester.LimitBetween("MspVout", 13.0, 14.6),
            ),
            "ScaleFactor": 1000,
        },
        "24": {
            "Limits": _common
            + (
                libtester.LimitBetween("OutOCP", 10.0, 12.0),
                libtester.LimitBetween("BattOCP", 6.0, 9.0),
                libtester.LimitLow("InOCP", 26.0),
                libtester.LimitPercent("VoutPreCal", 27.6, 2.6),
                libtester.LimitDelta("VoutPostCal", 27.6, _cal_factor * 0.25),
                libtester.LimitBetween("MspVout", 26.0, 29.2),
            ),
            "ScaleFactor": 500,
        },
    }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]["Limits"], Devices, Sensors, Measurements
        )
        self.steps = (
            tester.TestStep("Prepare", self._step_prepare),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Calibration", self._step_cal),
            tester.TestStep("OCP", self._step_ocp),
        )
        self.devices["msp"].scaling(self.limitdata[self.parameter]["ScaleFactor"])

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare: Dc input, measure."""
        dev["dcs_vccbias"].output(self._vcc_bias_set, output=True)
        self.measure(
            (
                "dmm_lock",
                "dmm_vccbiasext",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board."""
        try:
            self._tosbsl(dev)
            dev["dcs_vccbias"].output(0.0, output=False, delay=1)
        except tosbsl.BSLException as exc:  # Change exception into test fail
            _measurement = tester.Measurement(
                libtester.LimitRegExp(
                    name="Program", limit="ok", doc="Programming succeeded"
                ),
                tester.sensor.Mirror(),
            )
            _measurement.sensor.store(str(exc))
            _measurement()

    def _tosbsl(self, dev):
        """Program the board.

        Notes from the BCE282 Testing Notes:
        The bootloader software is programmed into the MSP430 processor at
        the factory and cannot be erased. This software requires a password
        to be sent with any command that can read or write the internal
        Flash as a security measure. This password consists of a dump of
        the top 32 bytes of Flash memory, so it is a run of 32 0xFF values
        for an unprogrammed part, which allows a fresh part to be programmed
        initially. If a previous version of the software is installed on the
        BCE282, the required password can be read using a command from
        the serial port.

        Performing a mass erase will erase some further special locations
        in Flash that are factory programmed with values for calibrating
        the on chip oscillator. If the contents of these locations are lost
        then the processor becomes useless as the on-chip oscillator
        frequency can no longer be set to a sufficient accuracy for
        reliable timing or serial comms. So when re-programming a part it
        is essential that these values be saved and restored.

        """
        # Get any existing password & write to MSP_PASSWORD file
        with dev["msp"] as msp:
            msp.measurement_fail_on_error = False
            password = None
            try:  # Fails if device has never been programmed
                password = "@ffe0\n{0}\nq\n".format(msp["PASSWD"])
                with self.msp_password.open("w") as fout:
                    fout.write(password)
            except share.console.Error:
                pass
            finally:
                msp.measurement_fail_on_error = True
        with dev["rla_prog"]:
            # BSL serial port for programming MSP430
            bsl_port = share.config.Fixture.port("020827", "BSL")
            # STEP 1 - SAVE INTERNAL CALIBRATION
            sys.argv = (
                [
                    "",
                    "--comport={0}".format(bsl_port),
                    "--slow",
                ]
                + (
                    [
                        "-P",
                        str(self.msp_password),
                    ]
                    if password
                    else []
                )
                + [
                    "--upload=0x10C0",
                    "--size=64",
                    "--ti",
                ]
            )
            tosbsl.main()
            # Write TI Text format calibration data to a file for use later
            with self.msp_savefile.open("w") as fout:
                for aline in tosbsl.SAVEDATA:
                    fout.write(aline + "\n")
            # STEP 2 - ERASE & RESTORE INTERNAL CALIBRATION
            sys.argv = [
                "",
                "--comport={0}".format(bsl_port),
                "--slow",
                "--masserase",
                "--program",
                str(self.msp_savefile),
            ]
            tosbsl.main()
            # STEP 3 - PROGRAM
            sys.argv = [
                "",
                "--comport={0}".format(bsl_port),
                "--slow",
                "--program",
                str(pathlib.Path(__file__).parent / self._hexfile),
            ]
            tosbsl.main()

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up the unit at 240Vac and measure voltages at min load."""
        dev["acsource"].output(voltage=240.0, output=True, delay=1.0)
        dev["dcl_vbat"].output(0.1, output=True)
        self.measure(
            (
                "dmm_vac",
                "dmm_vbus",
                "dmm_vccpri",
                "dmm_vccbias",
                "dmm_vbatoff",
                "dmm_alarmclose",
            ),
            timeout=5,
        )
        dev["dcl_vbat"].output(0.0)

    @share.teststep
    def _step_cal(self, dev, mes):
        """Calibration."""
        with dev["msp"] as msp:
            msp.initialise()
            mes["msp_status"]()
            msp.filter_reload()
            mes["msp_vout"]()
            dmm_V = mes["dmm_voutpre"].stable(delta=0.005).value1
            msp["CAL-V"] = dmm_V
            mes["dmm_voutpost"].stable(delta=0.005)
            msp["NV-WRITE"] = True
            mes["msp_status"]()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        self.measure(("dmm_alarmopen", "ramp_battocp"), timeout=5)
        dev["dcl_vbat"].output(0.0)
        mes["ramp_outocp"](timeout=5)
        dev["dcl_vout"].output(0.0)


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("acsource", tester.ACSource, "ACS"),
            ("discharge", tester.Discharge, "DIS"),
            ("dcs_vccbias", tester.DCSource, "DCS1"),
            ("dcs_vcom", tester.DCSource, "DCS2"),
            ("dcl_vout", tester.DCLoad, "DCL1"),
            ("dcl_vbat", tester.DCLoad, "DCL2"),
            ("rla_prog", tester.Relay, "RLA1"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console to communicate with the MSP430
        self["msp_ser"] = serial.Serial(baudrate=57600, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self["msp_ser"].port = share.config.Fixture.port("020827", "CON")
        # MSP430 Console driver
        self["msp"] = console.Console(self["msp_ser"])
        # Apply power to fixture circuits.
        self["dcs_vcom"].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self["dcs_vcom"].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self["msp"].close()
        self["acsource"].reset()
        self["dcl_vout"].output(2.0)
        self["dcl_vbat"].output(2.0)
        time.sleep(1)
        self["discharge"].pulse()
        for ld in ("dcl_vout", "dcl_vbat"):
            self[ld].output(0.0, output=False)
        for dcs in ("dcs_vccbias",):
            self[dcs].output(0.0, output=False)
        self["rla_prog"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        msp = self.devices["msp"]
        sensor = tester.sensor
        self["lock"] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self["vac"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["vbus"] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self["vcc_pri"] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self["vcc_bias"] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self["vout"] = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self["vbat"] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self["alarm"] = sensor.Res(dmm, high=9, low=5, rng=100000, res=1)
        self["msp_stat"] = sensor.Keyed(msp, "MSP-STATUS")
        self["msp_stat"].doc = "MSP430 console"
        self["msp_vo"] = sensor.Keyed(msp, "MSP-VOUT")
        self["msp_vo"].doc = "MSP430 console"
        low, high = self.limits["OutOCP"].limit
        self["ocp_out"] = sensor.Ramp(
            stimulus=self.devices["dcl_vout"],
            sensor=self["vout"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=low - 0.5, stop=high + 0.5, step=0.05),
            delay=0.05,
        )
        low, high = self.limits["BattOCP"].limit
        self["ocp_batt"] = sensor.Ramp(
            stimulus=self.devices["dcl_vbat"],
            sensor=self["vbat"],
            detect_limit=self.limits["InOCP"],
            ramp_range=sensor.RampRange(start=low - 0.5, stop=high + 0.5, step=0.05),
            delay=0.05,
        )


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_lock", "FixtureLock", "lock", ""),
                ("dmm_vac", "Vac", "vac", ""),
                ("dmm_vbus", "Vbus", "vbus", ""),
                ("dmm_vccpri", "VccPri", "vcc_pri", ""),
                ("dmm_vccbiasext", "VccBiasExt", "vcc_bias", ""),
                ("dmm_vccbias", "VccBias", "vcc_bias", ""),
                ("dmm_vbatoff", "VbatOff", "vbat", ""),
                ("dmm_alarmclose", "AlarmClosed", "alarm", ""),
                ("dmm_alarmopen", "AlarmOpen", "alarm", ""),
                ("dmm_voutpre", "VoutPreCal", "vout", "Output before Calibration"),
                ("dmm_voutpost", "VoutPostCal", "vout", "Output after Calibration"),
                ("ramp_outocp", "OutOCP", "ocp_out", ""),
                ("ramp_battocp", "BattOCP", "ocp_batt", ""),
                (
                    "msp_status",
                    "Status 0",
                    "msp_stat",
                    "Ask the MSP430 to report Status",
                ),
                (
                    "msp_vout",
                    "MspVout",
                    "msp_vo",
                    "Ask the MSP430 to report output voltage",
                ),
            )
        )
