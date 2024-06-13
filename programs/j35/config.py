#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""J35 Configuration."""

import enum
import logging
import math

from attrs import define, field, validators

import libtester


def get(parameter, uut):
    """Get a configuration based on the parameter and lot.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "A": J35A,
        "AS": ASPower,
        "B": J35B,
        "BL": J35BL,
        "C": J35C,
        "D": J35D,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


class Type(enum.IntEnum):
    """Product type numbers for hardware revisions."""

    A = 1
    B = 2
    C = 3
    D = 4
    BL = 5


@define
class _Values:
    """Adjustable configuration data values."""

    sw_version = field(validator=validators.instance_of(str))
    hw_version = field(validator=validators.instance_of(tuple))
    output_count = field(validator=validators.instance_of(int))
    ocp_set = field(validator=validators.instance_of(float))
    solar = field(validator=validators.instance_of(bool))
    canbus = field(validator=validators.instance_of(bool))
    air = field(validator=validators.instance_of(bool))


class J35:
    """Base configuration for J35."""

    # Available software versions
    sw_13 = "1.3.15775.997"  # For 'A' & 'B' < Rev 8
    sw_15 = "1.5.17467.1373"  # Rev 12 release
    sw_bld = "1.5.20386.1374"  # Rev 13 release
    sw_16 = "1.6.7634.1421"  # Rev 14 release
    # These values get set per Product type & revision
    sw_version = None
    hw_version = None
    output_count = None
    ocp_set = None
    solar = None
    canbus = None
    air = None
    # General parameters used in testing the units
    # Injected voltages
    #  Battery bus
    vbat_inject = 12.6
    #  Aux or Solar inputs
    aux_solar_inject = 13.5
    # AC voltage powering the unit
    ac_volt = 240.0
    ac_freq = 50.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # Output set points when running in manual mode
    vout_set = 12.8
    ocp_man_set = 35.0
    # Battery load current
    batt_current = 4.0
    # Load on each output channel
    load_per_output = 2.0
    # Test limits common to all tests and versions
    _base_limits_all = (libtester.LimitRegExp("SwVer", "None", doc="Software version"),)
    # Initial Test limits common to all versions
    _base_limits_initial = _base_limits_all + (
        libtester.LimitDelta("ACin", ac_volt, delta=5.0, doc="AC input voltage"),
        libtester.LimitDelta(
            "Vbus", ac_volt * math.sqrt(2), delta=10.0, doc="Peak of AC input"
        ),
        libtester.LimitBetween("12Vpri", 11.5, 13.0, doc="12Vpri rail"),
        libtester.LimitPercent(
            "Vload", vout_set, percent=3.0, doc="AC-DC convertor voltage setpoint"
        ),
        libtester.LimitLow("VloadOff", 0.5, doc="When output is OFF"),
        libtester.LimitDelta(
            "VbatIn",
            vbat_inject,
            delta=1.0,
            doc="Voltage at Batt when 12.6V is injected into Batt",
        ),
        libtester.LimitDelta(
            "VfuseIn",
            vbat_inject,
            delta=1.0,
            doc="Voltage after fuse when 12.6V is injected into Batt",
        ),
        libtester.LimitDelta(
            "VbatOut",
            aux_solar_inject,
            delta=0.5,
            doc="Voltage at Batt when 13.5V is injected into Aux",
        ),
        libtester.LimitDelta(
            "Vbat", vout_set, delta=0.2, doc="Voltage at Batt when unit is running"
        ),
        libtester.LimitPercent(
            "VbatLoad",
            vout_set,
            percent=5.0,
            doc="Voltage at Batt when unit is running under load",
        ),
        libtester.LimitDelta(
            "Vair",
            aux_solar_inject,
            delta=0.5,
            doc="Voltage at Air when 13.5V is injected into Solar",
        ),
        libtester.LimitPercent(
            "3V3U",
            3.30,
            percent=1.5,
            doc="3V3 unswitched when 12.6V is injected into Batt",
        ),
        libtester.LimitPercent("3V3", 3.30, percent=1.5, doc="3V3 internal rail"),
        libtester.LimitBetween("15Vs", 11.5, 13.0, doc="15Vs internal rail"),
        libtester.LimitDelta("FanOn", vout_set, delta=1.0, doc="Fan running"),
        libtester.LimitLow("FanOff", 0.5, doc="Fan not running"),
        libtester.LimitPercent(
            "ARM-AuxV",
            aux_solar_inject,
            percent=2.0,
            delta=0.3,
            doc="ARM Aux voltage reading",
        ),
        libtester.LimitBetween("ARM-AuxI", 0.0, 1.5, doc="ARM Aux current reading"),
        libtester.LimitInteger("Vout_OV", 0, doc="Over-voltage not triggered"),
        libtester.LimitPercent(
            "ARM-AcV", ac_volt, percent=4.0, delta=1.0, doc="ARM AC voltage reading"
        ),
        libtester.LimitPercent(
            "ARM-AcF", ac_freq, percent=4.0, delta=1.0, doc="ARM AC frequency reading"
        ),
        libtester.LimitBetween(
            "ARM-SecT", 8.0, 70.0, doc="ARM secondary temperature sensor"
        ),
        libtester.LimitPercent(
            "ARM-Vout", vout_set, percent=2.0, delta=0.1, doc="ARM measured Vout"
        ),
        libtester.LimitBetween("ARM-Fan", 0, 100, doc="ARM fan speed"),
        libtester.LimitPercent(
            "ARM-BattI",
            batt_current,
            percent=1.7,
            delta=1.0,
            doc="ARM battery current reading",
        ),
        libtester.LimitDelta(
            "ARM-LoadI", load_per_output, delta=0.9, doc="ARM output current reading"
        ),
        libtester.LimitInteger("ARM-RemoteClosed", 1),
        libtester.LimitDelta("CanPwr", vout_set, delta=1.8, doc="CAN bus power supply"),
        libtester.LimitInteger(
            "LOAD_SET", 0x5555555, doc="ARM output load enable setting"
        ),
        libtester.LimitInteger(
            "CAN_BIND", 1 << 28, doc="ARM reports CAN bus operational"
        ),
        libtester.LimitLow("InOCP", vout_set - 1.2, doc="Output is in OCP"),
        libtester.LimitLow("FixtureLock", 200, doc="Test fixture lid microswitch"),
        libtester.LimitBoolean(
            "Solar-Status", True, doc="Solar Comparator Status is set"
        ),
        libtester.LimitBoolean("DetectCal", True, doc="Solar comparator calibrated"),
    )
    # Final Test limits common to all versions
    _base_limits_final = _base_limits_all + (
        libtester.LimitLow("FanOff", 1.0, doc="No airflow seen"),
        libtester.LimitHigh("FanOn", 10.0, doc="Airflow seen"),
        libtester.LimitDelta("Can12V", 12.5, delta=2.0, doc="CAN_POWER rail"),
        libtester.LimitLow("Can0V", 0.5, doc="CAN BUS removed"),
        libtester.LimitLow("InOCP", 11.6, doc="Output voltage to detect OCP"),
    )
    # Internal data storage
    _rev_data = None  # Revision data dictionary

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.sw_version = values.sw_version
        cls.hw_version = values.hw_version
        cls.output_count = values.output_count
        cls.ocp_set = values.ocp_set
        cls.solar = values.solar
        cls.canbus = values.canbus
        cls.air = values.air


class J35A(J35):
    """J35A configuration."""

    # Output set points when running in manual mode
    ocp_man_set = 20.0
    _rev12_values = _Values(
        sw_version=J35.sw_15,
        hw_version=(12, Type.A.value, "A"),
        output_count=7,
        ocp_set=20.0,
        solar=False,
        canbus=True,
        air=False,
    )
    _rev_data = {
        None: _rev12_values,
        # Rev 13 never built
        "12": _rev12_values,
        "11": _Values(
            sw_version=J35.sw_15,
            hw_version=(11, Type.A.value, "A"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=True,
            air=False,
        ),
        "10": _Values(
            sw_version=J35.sw_15,
            hw_version=(10, Type.A.value, "A"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=True,
            air=False,
        ),
        "9": _Values(
            sw_version=J35.sw_15,
            hw_version=(9, Type.A.value, "B"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=True,
            air=False,
        ),
        "8": _Values(
            sw_version=J35.sw_15,
            hw_version=(8, Type.A.value, "C"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=True,
            air=False,
        ),
        # Rev <8 uses an older software version
        # No Rev 4,5,6 created
        # No Rev 3 production
        "2": _Values(
            sw_version=J35.sw_13,
            hw_version=(2, Type.A.value, "B"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=False,
            air=False,
        ),
        "1": _Values(
            sw_version=J35.sw_13,
            hw_version=(1, Type.A.value, "B"),
            output_count=7,
            ocp_set=20.0,
            solar=False,
            canbus=False,
            air=False,
        ),
    }

    @classmethod
    def limits_initial(cls):
        """J35-A initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + (
            libtester.LimitPercent(  # Not used. Needed by Sensors
                "SolarCutoffPre",
                14.125,
                percent=6,
                doc="Solar Cut-Off voltage threshold uncertainty",
            ),
            libtester.LimitBetween(  # Not used. Needed by Sensors
                "SolarCutoff", 13.75, 14.5, doc="Solar Cut-Off voltage threshold range"
            ),
            libtester.LimitPercentLoHi(
                "OCP_pre",
                cls.ocp_set,
                cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 10.0,
                doc="OCP trip range before adjustment",
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 10.0, doc="OCP trip range after adjustment"
            ),
        )

    @classmethod
    def limits_final(cls):
        """J35-A final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final + (
            libtester.LimitDelta("Vout", 12.8, delta=0.2, doc="No load output voltage"),
            libtester.LimitPercent(
                "Vload", 12.8, percent=5, doc="Loaded output voltage"
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 10.0, doc="OCP trip current"
            ),
        )


class J35B(J35):
    """J35B configuration."""

    _rev12_values = _Values(
        sw_version=J35.sw_15,
        hw_version=(12, Type.B.value, "A"),
        output_count=14,
        ocp_set=35.0,
        solar=True,
        canbus=True,
        air=False,
    )
    _rev_data = {
        None: _rev12_values,
        # Rev 13 never built
        "12": _rev12_values,
        "11": _Values(
            sw_version=J35.sw_15,
            hw_version=(11, Type.B.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=False,
        ),
        "10": _Values(
            sw_version=J35.sw_15,
            hw_version=(10, Type.B.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=False,
        ),
        "9": _Values(
            sw_version=J35.sw_15,
            hw_version=(9, Type.B.value, "B"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=False,
        ),
        "8": _Values(
            sw_version=J35.sw_15,
            hw_version=(8, Type.B.value, "C"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=False,
        ),
        # Rev <8 uses an older software version
        # No Rev 5,6 created
        # No Rev 3,4 production
        "2": _Values(
            sw_version=J35.sw_13,
            hw_version=(2, Type.B.value, "D"),
            output_count=14,
            ocp_set=35.0,
            solar=False,
            canbus=False,
            air=False,
        ),
        "1": _Values(
            sw_version=J35.sw_13,
            hw_version=(1, Type.B.value, "B"),
            output_count=14,
            ocp_set=35.0,
            solar=False,
            canbus=False,
            air=False,
        ),
    }

    @classmethod
    def limits_initial(cls):
        """J35-B initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + (
            libtester.LimitPercent(
                "SolarCutoffPre",
                14.125,
                percent=6,
                doc="Solar Cut-Off voltage threshold uncertainty",
            ),
            libtester.LimitBetween(
                "SolarCutoff", 13.75, 14.5, doc="Solar Cut-Off voltage threshold range"
            ),
            libtester.LimitPercentLoHi(
                "OCP_pre",
                cls.ocp_set,
                cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 7.0,
                doc="OCP trip range before adjustment",
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 7.0, doc="OCP trip range after adjustment"
            ),
        )

    @classmethod
    def limits_final(cls):
        """J35-B final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final + (
            libtester.LimitDelta("Vout", 12.8, delta=0.2, doc="No load output voltage"),
            libtester.LimitPercent(
                "Vload", 12.8, percent=5, doc="Loaded output voltage"
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 7.0, doc="OCP trip current"
            ),
        )


class J35BL(J35B):
    """J35BL configuration."""

    _rev14_values = _Values(
        sw_version=J35.sw_16,
        hw_version=(14, Type.BL.value, "A"),
        output_count=14,
        ocp_set=35.0,
        solar=True,
        canbus=True,
        air=False,
    )
    _rev_data = {
        None: _rev14_values,
        "14": _rev14_values,
        "13": _Values(
            sw_version=J35.sw_bld,
            hw_version=(13, Type.BL.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=False,
        ),
    }


class J35C(J35):
    """J35C configuration."""

    _rev12_values = _Values(
        sw_version=J35.sw_15,
        hw_version=(12, Type.C.value, "A"),
        output_count=14,
        ocp_set=35.0,
        solar=True,
        canbus=True,
        air=True,
    )
    _rev_data = {
        None: _rev12_values,
        # Rev 13 never built
        "12": _rev12_values,
        "11": _Values(
            sw_version=J35.sw_15,
            hw_version=(11, Type.C.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "10": _Values(
            sw_version=J35.sw_15,
            hw_version=(10, Type.C.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "9": _Values(
            sw_version=J35.sw_15,
            hw_version=(9, Type.C.value, "B"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "8": _Values(
            sw_version=J35.sw_15,
            hw_version=(8, Type.C.value, "C"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "7": _Values(
            sw_version=J35.sw_15,
            hw_version=(7, Type.C.value, "C"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "6": _Values(
            sw_version=J35.sw_15,
            hw_version=(6, Type.C.value, "E"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        # No Rev 5 production
        # 469 x J35C were converted to J35B via PC 4885
        #   J35C Rev 4, Lots: A164211 (x135), A164309 (x265)
        "4": _Values(
            sw_version=J35.sw_15,
            hw_version=(4, Type.C.value, "B"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        # Rev 1-3 must be scrapped per MA-328
        "3": None,
        "2": None,
        "1": None,
    }

    @classmethod
    def limits_initial(cls):
        """J35-C initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + (
            libtester.LimitPercent(
                "SolarCutoffPre",
                14.125,
                percent=6,
                doc="Solar Cut-Off voltage threshold uncertainty",
            ),
            libtester.LimitBetween(
                "SolarCutoff", 14.0, 14.6, doc="Solar Cut-Off voltage threshold range"
            ),
            libtester.LimitPercentLoHi(
                "OCP_pre",
                cls.ocp_set,
                cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 7.0,
                doc="OCP trip range before adjustment",
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 7.0, doc="OCP trip range after adjustment"
            ),
        )

    @classmethod
    def limits_final(cls):
        """J35-C final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final + (
            libtester.LimitDelta("Vout", 12.8, delta=0.2, doc="No load output voltage"),
            libtester.LimitPercent(
                "Vload", 12.8, percent=5, doc="Loaded output voltage"
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 7.0, doc="OCP trip current"
            ),
        )


class J35D(J35):
    """J35D configuration."""

    _rev14_values = _Values(
        sw_version=J35.sw_16,
        hw_version=(14, Type.D.value, "A"),
        output_count=14,
        ocp_set=35.0,
        solar=True,
        canbus=True,
        air=False,  # No AIR on Rev 14
    )
    _rev_data = {
        None: _rev14_values,
        "14": _rev14_values,
        "13": _Values(
            sw_version=J35.sw_bld,
            hw_version=(13, Type.D.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "12": _Values(
            sw_version=J35.sw_15,
            hw_version=(12, Type.D.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "11": _Values(
            sw_version=J35.sw_15,
            hw_version=(11, Type.D.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "10": _Values(
            sw_version=J35.sw_15,
            hw_version=(10, Type.D.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
        "9": _Values(
            sw_version=J35.sw_15,
            hw_version=(9, Type.D.value, "B"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
    }

    @classmethod
    def limits_initial(cls):
        """J35-D initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + (
            libtester.LimitPercent(
                "SolarCutoffPre",
                14.3,
                percent=6,
                doc="Solar Cut-Off voltage threshold uncertainty",
            ),
            libtester.LimitBetween(
                "SolarCutoff", 14.0, 14.6, doc="Solar Cut-Off voltage threshold range"
            ),
            libtester.LimitPercentLoHi(
                "OCP_pre",
                cls.ocp_set,
                cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 7.0,
                doc="OCP trip range before adjustment",
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set, 4.0, 7.0, doc="OCP trip range after adjustment"
            ),
        )

    @classmethod
    def limits_final(cls):
        """J35-D final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final + (
            libtester.LimitDelta("Vout", 14.0, delta=0.2, doc="No load output voltage"),
            libtester.LimitPercent(
                "Vload", 14.0, percent=5, doc="Loaded output voltage"
            ),
            libtester.LimitPercentLoHi(
                "OCP", cls.ocp_set * (12.8 / 14.0), 4.0, 7.0, doc="OCP trip current"
            ),
        )


class ASPower(J35D):
    """ASPower configuration."""

    _rev2_values = _Values(
        sw_version=J35.sw_16,
        hw_version=(2, Type.D.value, "A"),
        output_count=14,
        ocp_set=35.0,
        solar=True,
        canbus=True,
        air=True,
    )
    _rev_data = {
        None: _rev2_values,
        "2": _rev2_values,
        "1": _Values(
            sw_version=J35.sw_bld,
            hw_version=(1, Type.D.value, "A"),
            output_count=14,
            ocp_set=35.0,
            solar=True,
            canbus=True,
            air=True,
        ),
    }
