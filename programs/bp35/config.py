#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""BP35 / BP35-II Configurations."""

import enum
import logging

from attrs import define, field, validators

import libtester


def get(parameter, uut):
    """Get a configuration based on the parameter and lot.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "SR": BP35SR,
        "HA": BP35HA,
        "PM": BP35PM,
        "SR2": BP35IISR,
        "HA2": BP35IIHA,
        "SI2": BP35IISI,
        "UHA2": BP35IIUSHA,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


class Type(enum.IntEnum):
    """Product type numbers for hardware revisions."""

    SR = 1
    PM = 2
    SI = 2
    HA = 3


@define
class _Values:
    """Adjustable configuration data values."""

    hw_version = field(validator=validators.instance_of(tuple))
    arm_sw_version = field(validator=validators.instance_of(str))


class BP35:
    """Base configuration."""

    is_2 = False
    # Software versions
    arm_sw_version = "2.0.17344.4603"  # Software Rev 14
    pic_sw_version = "1.6.20227.735"  # Software Rev 11
    fixture_num = "027176"  # BP35 Fixture
    pic_hw_version = 4
    # SR Solar Reg settings
    sr_vset = 13.650
    sr_vset_settle = 0.05
    sr_iset = 30.0
    sr_ical = 10.0
    sr_vin = 20.0
    sr_vin_pre_percent = 6.0
    sr_vin_post_percent = 1.5
    # This value is set per Product type & revision
    arm_hw_version = None
    # Injected Vbat & Vaux
    vbat_in = 12.4
    vaux_in = 13.5
    # PFC settling level
    pfc_stable = 0.05
    # Converter loading
    iload = 28.0
    ibatt = 4.0
    # Other settings
    vac = 240.0
    outputs = 14
    vout_set = 12.8
    ocp_set = 35.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # Test limits common to all tests and versions
    _base_limits_all = (
        libtester.LimitRegExp("ARM-SwVer", "None", doc="Software version"),
        libtester.LimitDelta("Vload", 12.45, 0.45, doc="Load output present"),
        libtester.LimitLow("InOCP", 11.6, doc="Output voltage in OCP"),
        libtester.LimitPercent("OCP", ocp_set, 4.0, doc="After adjustment"),
    )
    # Initial Test limits common to all versions
    _base_limits_initial = _base_limits_all + (
        libtester.LimitLow("FixtureLock", 200, doc="Contacts closed"),
        libtester.LimitDelta("HwVer8", 4400.0, 250.0, doc="Hardware Rev ≥8"),
        libtester.LimitDelta("ACin", vac, 5.0, doc="Injected AC voltage present"),
        libtester.LimitBetween("Vpfc", 397.0, 429.0, doc="PFC running"),
        libtester.LimitLow("VloadOff", 0.5, doc="Load output off"),
        libtester.LimitDelta("VbatIn", 12.0, 0.5, doc="Injected Vbatt present"),
        libtester.LimitBetween("Vbat", 12.2, 13.0, doc="Vbatt present"),
        libtester.LimitDelta("Vaux", 13.4, 0.4, doc="Vaux present"),
        libtester.LimitDelta("3V3", 3.30, 0.05, doc="3V3 present"),
        libtester.LimitDelta("FanOn", 12.5, 0.5, doc="Fans ON"),
        libtester.LimitLow("FanOff", 0.5, doc="Fans OFF"),
        libtester.LimitPercent(
            "OCP_pre", ocp_set, 4.0 + ocp_adjust_percent, doc="Before adjustment"
        ),
        libtester.LimitDelta("ARM-AcV", vac, 10.0, doc="AC voltage"),
        libtester.LimitDelta("ARM-AcF", 50.0, 3.0, doc="AC frequency"),
        libtester.LimitBetween("ARM-SecT", 8.0, 70.0, doc="Reading ok"),
        libtester.LimitDelta("ARM-Vout", 12.45, 0.45),
        libtester.LimitBetween("ARM-Fan", 0, 100, doc="Fan running"),
        libtester.LimitDelta("ARM-LoadI", 2.1, 0.9, doc="Load current flowing"),
        libtester.LimitDelta("ARM-BattI", ibatt, 1.0, doc="Battery current flowing"),
        libtester.LimitDelta("ARM-BusI", iload + ibatt, 3.0, doc="Bus current flowing"),
        libtester.LimitPercent(
            "ARM-AuxV", vaux_in, percent=2.0, delta=0.3, doc="AUX present"
        ),
        libtester.LimitBetween("ARM-AuxI", 0.0, 1.5, doc="AUX current flowing"),
        libtester.LimitInteger("ARM-RemoteClosed", 1, doc="REMOTE input connected"),
        libtester.LimitDelta(
            "CanPwr", vout_set, delta=3.0, doc="CAN bus power present"
        ),
        libtester.LimitRegExp("CAN_RX", r"^RRQ,32,0", doc="Expected CAN message"),
        libtester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN comms established"),
        libtester.LimitInteger("Vout_OV", 0, doc="Over-voltage not triggered"),
        libtester.LimitRegExp("Reply", "^OK$"),
        # SR limits
        libtester.LimitDelta("SolarVcc", 3.3, 0.1, doc="Vcc present"),
        libtester.LimitDelta("SolarVin", sr_vin, 0.5, doc="Input present"),
        libtester.LimitPercent("VsetPre", sr_vset, 6.0, doc="Vout before calibration"),
        libtester.LimitPercent("VsetPost", sr_vset, 1.5, doc="Vout after calibration"),
        libtester.LimitPercentLoHi(
            "ARM-IoutPre", sr_ical, 9.0, 20.0, doc="Iout before calibration"
        ),
        libtester.LimitPercent(
            "ARM-IoutPost", sr_ical, 3.0, doc="Iout after calibration"
        ),
        libtester.LimitPercent(
            "ARM-SolarVin-Pre", sr_vin, sr_vin_pre_percent, doc="Vin before calibration"
        ),
        libtester.LimitPercent(
            "ARM-SolarVin-Post",
            sr_vin,
            sr_vin_post_percent,
            doc="Vin after calibration",
        ),
        libtester.LimitInteger("SR-Alive", 1, doc="Detected"),
        libtester.LimitInteger("SR-Relay", 1, doc="Input relay ON"),
        libtester.LimitInteger("SR-Error", 0, doc="No error"),
        # PM limits
        libtester.LimitInteger("PM-Alive", 1, doc="Detected"),
        libtester.LimitDelta(
            "ARM-PmSolarIz-Pre", 0, 0.6, doc="Zero reading before cal"
        ),
        libtester.LimitDelta(
            "ARM-PmSolarIz-Post", 0, 0.1, doc="Zero reading after cal"
        ),
    )
    # BP35xx Rev 3-5 control rails
    _crail_3_5 = (
        libtester.LimitBetween("12Vpri", 11.5, 13.0, doc="Control rail present"),
        libtester.LimitBetween("15Vs", 11.5, 13.0, doc="Control rail present"),
    )
    # BP35-II Rev 6 control rails
    _crail_6 = (
        libtester.LimitBetween("12Vpri", 13.6, 15.0, doc="Control rail present"),
        libtester.LimitBetween("15Vs", 14.3, 14.9, doc="Control rail present"),
    )
    # Final Test limits common to all versions
    _base_limits_final = _base_limits_all + (
        libtester.LimitDelta("Can12V", 12.0, delta=3.0, doc="CAN_POWER rail"),
        libtester.LimitLow("Can0V", 0.5, doc="CAN BUS removed"),
        libtester.LimitHigh("FanOn", 10.0, doc="Fan running"),
        libtester.LimitLow("FanOff", 1.0, doc="Fan not running"),
        libtester.LimitBetween("Vout", 12.0, 12.9, doc="No load output voltage"),
    )
    # Internal data storage
    _rev = None  # Selected revision
    _rev_data = None  # Revision data dictionary

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        cls._rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", cls._rev)
        values = cls._rev_data[cls._rev]
        cls.arm_hw_version = values.hw_version
        cls.arm_sw_version = values.arm_sw_version

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final


class BP35_I(BP35):
    """BP35 series base configuration."""

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + cls._crail_3_5


class BP35SR(BP35_I):
    """BP35SR configuration."""

    is_pm = False
    _rev14_values = _Values(
        hw_version=(14, Type.SR.value, "A"), arm_sw_version=BP35_I.arm_sw_version
    )
    _rev6_values = _Values(
        hw_version=(6, Type.SR.value, "E"), arm_sw_version=BP35_I.arm_sw_version
    )
    _rev_data = {
        None: _rev14_values,
        "14": _rev14_values,
        "13": _Values(
            hw_version=(13, Type.SR.value, "D"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "12": _Values(
            hw_version=(12, Type.SR.value, "E"), arm_sw_version=BP35_I.arm_sw_version
        ),
        # No Rev 11 created
        "10": _Values(
            hw_version=(10, Type.SR.value, "G"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "9": _Values(
            hw_version=(9, Type.SR.value, "G"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "8": _Values(
            hw_version=(8, Type.SR.value, "I"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "7": _Values(
            hw_version=(7, Type.SR.value, "D"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "6": _rev6_values,
        # Rev 1-5 are Main PCB swaps
        "5": _rev6_values,
        "4": _rev6_values,
        "3": _rev6_values,
        "2": _rev6_values,
        "1": _rev6_values,
    }


class BP35HA(BP35SR):
    """BP35HA configuration."""

    _rev14_values = _Values(
        hw_version=(14, Type.HA.value, "A"), arm_sw_version=BP35_I.arm_sw_version
    )
    _rev_data = {
        None: _rev14_values,
        "14": _rev14_values,
        "13": _Values(
            hw_version=(13, Type.HA.value, "B"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "12": _Values(
            hw_version=(12, Type.HA.value, "C"), arm_sw_version=BP35_I.arm_sw_version
        ),
        # No Rev 11 created
        "10": _Values(
            hw_version=(10, Type.HA.value, "E"), arm_sw_version=BP35_I.arm_sw_version
        ),
        # No Rev 1-9 created
    }


class BP35PM(BP35_I):
    """BP35PM configuration."""

    is_pm = True
    # PM Solar Reg settings
    pm_zero_wait = 30  # Settling delay for zero calibration
    _rev14_values = _Values(
        hw_version=(14, Type.PM.value, "A"), arm_sw_version=BP35_I.arm_sw_version
    )
    _rev_data = {
        None: _rev14_values,
        "14": _rev14_values,
        "13": _Values(
            hw_version=(13, Type.PM.value, "B"), arm_sw_version=BP35_I.arm_sw_version
        ),
        "12": _Values(
            hw_version=(12, Type.PM.value, "C"), arm_sw_version=BP35_I.arm_sw_version
        ),
        # No Rev 11 created
        "10": _Values(
            hw_version=(10, Type.PM.value, "E"), arm_sw_version=BP35_I.arm_sw_version
        ),
        # No Rev 1-9 created
    }


class BP35_II(BP35):
    """Base configuration for BP35-II."""

    is_2 = True
    # ARM software version
    arm_5015 = "2.0.20330.5015"  # PC-24332 & MA-368 (All Rev 3)
    arm_5073 = "2.0.64652.5073"  # Rev 4 @ ECO-23109 & MA395, Rev 5, Rev 7
    arm_5090 = "2.0.1072.5090"  # Rev 6
    fixture_num = "034400"  # BP35-II Fixture

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple of limits

        """
        crails = {
            None: cls._crail_3_5,
            "7": cls._crail_3_5,
            "6": cls._crail_6,
            "5": cls._crail_3_5,
            "4": cls._crail_3_5,
            "3": cls._crail_3_5,
        }[cls._rev]
        return cls._base_limits_initial + crails


class BP35IISR(BP35_II):
    """BP35-IISR configuration."""

    is_pm = False
    _rev4_values = _Values(
        hw_version=(16, Type.SR.value, "B"), arm_sw_version=BP35_II.arm_5073
    )
    _rev_data = {
        # No Rev >4
        None: _rev4_values,
        "4": _rev4_values,
        "3": _Values(
            hw_version=(15, Type.SR.value, "E"), arm_sw_version=BP35_II.arm_5015
        ),
        # No Rev 1 or 2
    }


class BP35IIHA(BP35IISR):
    """BP35-IIHA configuration."""

    _rev7_values = _Values(
        hw_version=(19, Type.HA.value, "A"), arm_sw_version=BP35_II.arm_5073
    )
    _rev_data = {
        None: _rev7_values,
        "7": _rev7_values,
        "6": _Values(
            hw_version=(18, Type.HA.value, "A"), arm_sw_version=BP35_II.arm_5090
        ),
        "5": _Values(
            hw_version=(17, Type.HA.value, "A"), arm_sw_version=BP35_II.arm_5073
        ),
        "4": _Values(
            hw_version=(16, Type.HA.value, "B"), arm_sw_version=BP35_II.arm_5073
        ),
        "3": _Values(
            hw_version=(15, Type.HA.value, "E"), arm_sw_version=BP35_II.arm_5015
        ),
        # No Rev 1 or 2
    }


class BP35IISI(BP35_II):
    """BP35-IISI configuration."""

    is_pm = True
    # PM Solar Reg settings
    pm_zero_wait = 30  # Settling delay for zero calibration
    _rev7_values = _Values(
        hw_version=(19, Type.SI.value, "A"), arm_sw_version=BP35_II.arm_5073
    )
    _rev_data = {
        None: _rev7_values,
        "7": _rev7_values,
        "6": _Values(
            hw_version=(18, Type.SI.value, "A"), arm_sw_version=BP35_II.arm_5090
        ),
        "5": _Values(
            hw_version=(17, Type.SI.value, "A"), arm_sw_version=BP35_II.arm_5073
        ),
        "4": _Values(
            hw_version=(16, Type.SI.value, "B"), arm_sw_version=BP35_II.arm_5073
        ),
        "3": _Values(
            hw_version=(15, Type.SI.value, "E"), arm_sw_version=BP35_II.arm_5015
        ),
        # No Rev 1 or 2
    }


class BP35IIUSHA(BP35IISR):
    """BP35-IIUSHA configuration."""

    _rev6_values = _Values(
        hw_version=(19, Type.HA.value, "A"), arm_sw_version=BP35_II.arm_5073
    )
    _rev_data = {
        None: _rev6_values,
        "6": _rev6_values,
        "5": _Values(
            hw_version=(17, Type.HA.value, "A"), arm_sw_version=BP35_II.arm_5073
        ),
        "4": _Values(
            hw_version=(16, Type.HA.value, "B"), arm_sw_version=BP35_II.arm_5073
        ),
        # No Rev 1-3
    }

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + cls._crail_3_5
