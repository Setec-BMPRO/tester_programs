#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""CMR-SBP ALL Test Program."""

import datetime
import pathlib
import time
import serial

import libtester
import tester

import share
from . import ev2200
from . import cmrsbp


class Initial(share.TestSequence):
    """CMR-SBP Initial Test Program."""

    # PIC firmware image file
    pic_hex = "CMR-SBP-9.hex"
    # Test limits
    limitdata = (
        libtester.LimitDelta("Vbat", 12.0, 0.10),
        libtester.LimitBetween("VbatCharge", 11.8, 12.5),
        libtester.LimitDelta("Vcc", 3.3, 0.2),
        libtester.LimitBetween("VErase", 4.8, 5.05),
        libtester.LimitLow("IStart", 0.02),
        libtester.LimitBetween("Vchge", 12.8, 15.0),
        libtester.LimitDelta("Ibat", -2.00, 0.02),
        libtester.LimitLow("Final Not Connected", 1.0),
        libtester.LimitDelta("SenseRes", 250, 30),
        libtester.LimitDelta("Halfcell", 110, 10),
        libtester.LimitDelta("VChgeOn", 350, 50),
        libtester.LimitDelta("ErrVUncal", 0.0, 0.5),
        libtester.LimitDelta("ErrVCal", 0.0, 0.03),
        libtester.LimitDelta("ErrIUncal", 0.0, 0.060),
        libtester.LimitDelta("ErrICal", 0.0, 0.015),
        # 298K nominal +/- 2.5K in Kelvin (25C +/- 2.5C in Celsius).
        libtester.LimitDelta("BQ-Temp", 300, 4.5),
        # SerialDate
        libtester.LimitRegExp("CmrSerNum", r"^[9A-HJ-NP-V][1-9A-C][0-9]{5}F[0-9]{4}$"),
    )

    def open(self):
        """Prepare for testing."""
        Devices.fixture = self.fixture
        self.configure(self.limitdata, Devices, Sensors, MeasureIni)
        super().open()
        self.steps = (
            tester.TestStep("PowerUp", self._step_power_up),
            tester.TestStep("Program", self._step_program),
            tester.TestStep("CheckPicValues", self._step_check_pic_vals),
            tester.TestStep("CheckVcharge", self._step_check_vchge),
            tester.TestStep("CalBQvolts", self._step_calv),
            tester.TestStep("CalBQcurrent", self._step_cali),
        )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up with vbat.

        Check that a Final Unit is not connected.
        Apply vbat and measure voltages.

        """
        mes["dmm_NoFinal"](timeout=5)
        dev["rla_vbat"].set_on()
        dev["dcs_vbat"].output(12.20, output=True)
        self.measure(
            (
                "dmm_vbat",
                "dmm_Vcc",
            ),
            timeout=5,
        )

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the PIC micro."""
        with dev["rla_Erase"]:
            self.measure(
                (
                    "dmm_VErase",
                    "ProgramPIC",
                ),
                timeout=5,
            )

    @share.teststep
    def _step_check_pic_vals(self, dev, mes):
        """Check some values from the PIC.

        Power Comms interface and connect to PIC.
        Read PIC and check values.

        """
        dev["dcs_Vchg"].output(12.6, output=True, delay=15)
        dev["rla_Pic"].set_on(delay=2)
        cmr_data = dev["cmr"].read()
        mes["cmr_SenseRes"].sensor.store(cmr_data["SENSE RESISTOR READING"])
        mes["cmr_Halfcell"].sensor.store(cmr_data["HALF CELL READING"])
        mes["cmr_VChgeOn"].sensor.store(cmr_data["CHARGE INPUT READING"])
        self.measure(
            ("cmr_SenseRes", "cmr_Halfcell", "cmr_VChgeOn"),
        )

    @share.teststep
    def _step_check_vchge(self, dev, mes):
        """Check Vcharge."""
        dev["dcs_vbat"].output(0.0)
        dev["rla_vbat"].set_off()
        self.measure(("dmm_vbatChge", "dmm_Vcc"), timeout=5)
        dev["rla_vbat"].set_on()

    @share.teststep
    def _step_calv(self, dev, mes):
        """Calibrate vbat for BQ2060A."""
        try:
            evdev = dev["ev"]
            evdev.open()
            dev["dcs_vbat"].output(12.20)
            dev["dcs_Vchg"].output(0.0)
            dev["rla_Pic"].set_off()
            dev["rla_PicReset"].set_on(delay=3)
            dev["rla_EVM"].set_on()
            dmm_vbat = mes["dmm_vbat"](timeout=5).value1
            ev_data = evdev.read_vit()
            mes["bq_ErrVUncal"].sensor.store(dmm_vbat - ev_data["Voltage"])
            mes["bq_Temp"].sensor.store(ev_data["Temperature"])
            self.measure(("bq_ErrVUncal", "bq_Temp"))
            evdev.cal_v(dmm_vbat)
            ev_data = evdev.read_vit()
            mes["bq_ErrVCal"].sensor.store(dmm_vbat - ev_data["Voltage"])
            mes["bq_ErrVCal"]()
        except ev2200.Ev2200Error as err:
            EvError(err)

    @share.teststep
    def _step_cali(self, dev, mes):
        """Calibrate ibat for BQ2060A."""
        try:
            evdev = dev["ev"]
            dev["dcl_ibat"].output(2.0, True)
            dmm_ibat = mes["dmm_ibat"](timeout=5).value1
            time.sleep(3)
            ev_data = evdev.read_vit()
            mes["bq_ErrIUncal"].sensor.store(dmm_ibat - ev_data["Current"])
            mes["bq_ErrIUncal"]()
            evdev.cal_i(dmm_ibat)
            ev_data = evdev.read_vit()
            mes["bq_ErrICal"].sensor.store(dmm_ibat - ev_data["Current"])
            mes["bq_ErrICal"]()
            dev["dcl_ibat"].output(0.0)
        except ev2200.Ev2200Error as err:
            EvError(err)


class SerialDate(share.TestSequence):
    """CMR-SBP SerialDate Test Program."""

    def open(self):
        """Prepare for testing."""
        Devices.fixture = self.fixture
        self.configure(Initial.limitdata, Devices, Sensors, MeasureIni)
        super().open()
        self.steps = (tester.TestStep("SerialDate", self._step_sn_date),)

    @share.teststep
    def _step_sn_date(self, dev, mes):
        """Write SerialNo & Manufacturing Datecode into EEPROM of BQ2060A."""
        try:
            evdev = dev["ev"]
            evdev.open()
            mes["dmm_NoFinal"](timeout=5)
            dev["rla_vbat"].set_on()
            dev["dcs_vbat"].output(12.20, output=True)
            dev["rla_PicReset"].set_on(delay=2)
            dev["rla_EVM"].set_on()
            sernum = mes["ui_SnEntry"]().value1[-4:]  # Last 4 digits only
            current_date = datetime.date.today().isoformat()
            evdev.sn_date(datecode=current_date, serialno=sernum)
        except ev2200.Ev2200Error as err:
            EvError(err)


class Final(share.TestSequence):
    """CMR-SBP Final Test Program."""

    # Common test limits
    _common = (
        libtester.LimitDelta("ErrV", 0.0, 0.03),
        libtester.LimitHigh("CycleCnt", 1.0),
        libtester.LimitBoolean("RelrnFlg", False),
        libtester.LimitInteger("RotarySw", 256),
        libtester.LimitDelta("Halfcell", 400, 50),
        libtester.LimitBoolean("VFCcalStatus", True),
        libtester.LimitRegExp("SerNumChk", "None"),
    )
    # Common to both sets of 8Ah
    _common8 = _common + (
        libtester.LimitBetween("VbatIn", 12.8, 15.0),
        libtester.LimitBetween("SenseRes", 39.0, 91.0),
        libtester.LimitDelta("StateOfCharge", 100.0, 10.5),
        libtester.LimitRegExp(
            "CmrSerNum", r"^[9A-HJ-NP-V][1-9A-C](36861|40214)F[0-9]{4}$"
        ),
    )
    # Common to both sets of 13Ah
    _common13 = _common + (
        libtester.LimitBetween("VbatIn", 12.8, 15.0),
        libtester.LimitBetween("SenseRes", 221.0, 280.0),
        libtester.LimitDelta("StateOfCharge", 100.0, 10.5),
        libtester.LimitRegExp(
            "CmrSerNum", r"^[9A-HJ-NP-V][1-9A-C](36862|40166)F[0-9]{4}$"
        ),
    )
    # Common to both sets of 17Ah
    _common17 = _common + (
        libtester.LimitBetween("VbatIn", 11.8, 15.0),  # Due to <30% charge
        libtester.LimitBetween("SenseRes", 400.0, 460.0),
        libtester.LimitLow("StateOfCharge", 30.0),
        libtester.LimitRegExp(
            "CmrSerNum", r"^[9A-HJ-NP-V][1-9A-C]403(15|23)F[0-9]{4}$"
        ),
    )
    # Test limit selection keyed by program parameter
    limitdata = {
        "8": _common8 + (libtester.LimitBetween("Capacity", 7000, 11000),),
        "8_RMA": _common8 + (libtester.LimitBetween("Capacity", 6400, 11000),),
        "13": _common13 + (libtester.LimitBetween("Capacity", 11000, 15000),),
        "13_RMA": _common13 + (libtester.LimitBetween("Capacity", 10700, 15000),),
        "17": _common17 + (libtester.LimitBetween("Capacity", 15500, 20000),),
        "17_RMA": _common17 + (libtester.LimitBetween("Capacity", 13900, 20000),),
    }

    def open(self):
        """Prepare for testing."""
        Devices.fixture = self.fixture
        self.configure(self.limitdata[self.parameter], Devices, Sensors, MeasureFin)
        super().open()
        self.steps = (
            tester.TestStep("Startup", self._step_startup),
            tester.TestStep("Verify", self._step_verify),
        )

    @share.teststep
    def _step_startup(self, dev, mes):
        """Power comms interface, connect to PIC."""
        sernum = mes["ui_SnEntry"]().value1
        self.limits["SerNumChk"].adjust(str(int(sernum[-4:])))
        dev["rla_Pic"].set_on()

    @share.teststep
    def _step_verify(self, dev, mes):
        """Read data broadcast from the PIC and verify values."""
        dmm_vbatIn = mes["dmm_vbatIn"](timeout=5).value1
        cmr_data = dev["cmr"].read()
        mes["cmr_vbatIn"].sensor.store(cmr_data["VOLTAGE"])
        mes["cmr_ErrV"].sensor.store(dmm_vbatIn - cmr_data["VOLTAGE"])
        mes["cmr_CycleCnt"].sensor.store(cmr_data["CYCLE COUNT"])
        status = self.bit_status(cmr_data["BATTERY MODE"], 7)
        mes["cmr_RelrnFlg"].sensor.store(status)
        mes["cmr_Sw"].sensor.store(cmr_data["ROTARY SWITCH READING"])
        mes["cmr_SenseRes"].sensor.store(cmr_data["SENSE RESISTOR READING"])
        mes["cmr_Capacity"].sensor.store(cmr_data["FULL CHARGE CAPACITY"])
        mes["cmr_RelStateCharge"].sensor.store(cmr_data["REL STATE OF CHARGE"])
        mes["cmr_Halfcell"].sensor.store(cmr_data["HALF CELL READING"])
        status = self.bit_status(cmr_data["PACK STATUS AND CONFIG"], 7)
        mes["cmr_VFCcalStatus"].sensor.store(status)
        mes["cmr_SerNum"].sensor.store(str(cmr_data["SERIAL NUMBER"]))
        self.measure(
            (
                "cmr_vbatIn",
                "cmr_ErrV",
                "cmr_CycleCnt",
                "cmr_RelrnFlg",
                "cmr_Sw",
                "cmr_SenseRes",
                "cmr_Capacity",
                "cmr_RelStateCharge",
                "cmr_Halfcell",
                "cmr_VFCcalStatus",
                "cmr_SerNum",
            ),
        )

    @staticmethod
    def bit_status(num, check_bit):
        """Check if a bit in an integer is 1 or 0.

        num - Integer.
        check_bit - Bit number to check.
        Return true if bit is set otherwise false.

        """
        mask = 1 << check_bit
        return True if num & mask else False


class EvError:
    """EV2200 error handler."""

    def __init__(self, err):
        """Generate a Measurement failure.

        @param err ev2200.Ev2200Error instance

        """
        tmp = tester.Measurement(
            libtester.LimitRegExp("Ev2200", "ok", doc="Command succeeded"),
            tester.sensor.Mirror(),
        )
        tmp.sensor.store(str(err))
        tmp.measure()  # Generates a test FAIL result


class Devices(share.Devices):
    """Devices."""

    fixture = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ("dmm", tester.DMM, "DMM"),
            ("dcs_Vchg", tester.DCSource, "DCS1"),
            ("dcs_Vcom", tester.DCSource, "DCS2"),
            ("dcl_ibat", tester.DCLoad, "DCL1"),
            ("rla_vbat", tester.Relay, "RLA5"),
            ("rla_PicReset", tester.Relay, "RLA6"),
            ("rla_Prog", tester.Relay, "RLA7"),
            ("rla_EVM", tester.Relay, "RLA8"),  # Enables the EV2200
            ("rla_Pic", tester.Relay, "RLA9"),  # Connect to PIC
            # Apply 5V to Vdd for Erasing PIC
            ("rla_Erase", tester.Relay, "RLA10"),
        ):
            self[name] = devtype(self.physical_devices[phydevname])
        self["dcs_vbat"] = tester.DCSourceParallel(
            (
                tester.DCSource(self.physical_devices["DCS3"]),
                tester.DCSource(self.physical_devices["DCS4"]),
                tester.DCSource(self.physical_devices["DCS5"]),
            )
        )
        # Apply power to fixture circuits.
        self["dcs_Vcom"].output(12.0, output=True, delay=10)
        self.add_closer(lambda: self["dcs_Vcom"].output(0.0, output=False))
        # Open serial connection to data monitor
        cmr_ser = serial.Serial(
            port=self.port("CMR"),
            baudrate=9600,
            timeout=0.1,
        )
        self["cmr"] = cmrsbp.CmrSbp(cmr_ser, data_timeout=10)
        self.add_closer(self["cmr"].close)
        # EV2200 board
        ev_ser = serial.Serial(baudrate=9600, timeout=4)
        # Set port separately, as we don't want it opened yet
        ev_ser.port = self.port("EV")
        self["ev"] = ev2200.EV2200(ev_ser)
        self["PicKit"] = tester.PicKit(
            (self.physical_devices["PICKIT"], self["rla_Prog"])
        )

    def reset(self):
        """Reset instruments."""
        self["ev"].close()
        for dcs in ("dcs_vbat", "dcs_Vchg"):
            self[dcs].output(0.0, False)
        self["dcl_ibat"].output(0.0)
        for rla in (
            "rla_vbat",
            "rla_PicReset",
            "rla_Prog",
            "rla_EVM",
            "rla_Pic",
            "rla_Erase",
        ):
            self[rla].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        for name in (
            "oMirvbatIn",
            "oMirCycleCnt",
            "oMirRelrnFlg",
            "oMirSenseRes",
            "oMirCapacity",
            "oMirRelStateCharge",
            "oMirHalfCell",
            "oMirVFCcalStatus",
            "oMirVChge",
            "oMirErrV",
            "oMirErrI",
            "oMirTemp",
            "oMirSw",
            "oMirSerNum",
        ):
            self[name] = sensor.Mirror()
        self["ovbatIn"] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self["ovbat"] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.0001)
        self["oVcc"] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self["oVchge"] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self["oibat"] = sensor.Vdc(
            dmm, high=4, low=2, rng=0.1, res=0.000001, scale=100.0
        )
        self["PicKit"] = sensor.PicKit(
            self.devices["PicKit"],
            pathlib.Path(__file__).parent / Initial.pic_hex,
            "18F252",
        )
        self["sn_entry_ini"] = sensor.DataEntry(
            message=tester.translate("cmrsbp_sn", "msgSnEntryIni"),
            caption=tester.translate("cmrsbp_sn", "capSnEntry"),
        )
        self["sn_entry_fin"] = sensor.DataEntry(
            message=tester.translate("cmrsbp_sn", "msgSnEntryFin"),
            caption=tester.translate("cmrsbp_sn", "capSnEntry"),
        )


class MeasureIni(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("cmr_SenseRes", "SenseRes", "oMirSenseRes", ""),
                ("cmr_Halfcell", "Halfcell", "oMirHalfCell", ""),
                ("cmr_VChgeOn", "VChgeOn", "oMirVChge", ""),
                ("bq_ErrVUncal", "ErrVUncal", "oMirErrV", ""),
                ("bq_ErrIUncal", "ErrIUncal", "oMirErrI", ""),
                ("bq_Temp", "BQ-Temp", "oMirTemp", ""),
                ("bq_ErrVCal", "ErrVCal", "oMirErrV", ""),
                ("bq_ErrICal", "ErrICal", "oMirErrI", ""),
                ("dmm_NoFinal", "Final Not Connected", "ovbatIn", ""),
                ("dmm_vbat", "Vbat", "ovbat", ""),
                ("dmm_vbatChge", "VbatCharge", "ovbat", ""),
                ("dmm_Vcc", "Vcc", "oVcc", ""),
                ("dmm_VErase", "VErase", "oVcc", ""),
                ("dmm_Vchge", "Vchge", "oVchge", ""),
                ("dmm_ibat", "Ibat", "oibat", ""),
                ("ui_SnEntry", "CmrSerNum", "sn_entry_ini", ""),
                ("ProgramPIC", "ProgramOk", "PicKit", ""),
            )
        )


class MeasureFin(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("ui_SnEntry", "CmrSerNum", "sn_entry_fin", ""),
                ("dmm_vbatIn", "VbatIn", "ovbatIn", ""),
                ("cmr_vbatIn", "VbatIn", "oMirvbatIn", ""),
                ("cmr_ErrV", "ErrV", "oMirErrV", ""),
                ("cmr_CycleCnt", "CycleCnt", "oMirCycleCnt", ""),
                ("cmr_RelrnFlg", "RelrnFlg", "oMirRelrnFlg", ""),
                ("cmr_Sw", "RotarySw", "oMirSw", ""),
                ("cmr_SenseRes", "SenseRes", "oMirSenseRes", ""),
                ("cmr_Capacity", "Capacity", "oMirCapacity", ""),
                ("cmr_RelStateCharge", "StateOfCharge", "oMirRelStateCharge", ""),
                ("cmr_Halfcell", "Halfcell", "oMirHalfCell", ""),
                ("cmr_VFCcalStatus", "VFCcalStatus", "oMirVFCcalStatus", ""),
                ("cmr_SerNum", "SerNumChk", "oMirSerNum", ""),
            )
        )
