#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Configuration."""

import logging

import attr
import tester

import share


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut setec.tester.UUT instance
    @return configuration class

    """
    config = {
        "101A": RVMN101A,
        "101B": RVMN101B,
        "101C": RVMN101C,
        "50": RVMN5x,
        "55": RVMN5x,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


@attr.s
class Values:

    """Adjustable configuration data values.

    These values get set per Product type & revision

    """

    nordic_image = attr.ib(validator=attr.validators.instance_of(str))
    arm_image = attr.ib(validator=attr.validators.instance_of(str))
    product_rev = attr.ib(validator=attr.validators.instance_of(str))
    hardware_rev = attr.ib()
    reversed_outputs = attr.ib(
        factory=dict, validator=attr.validators.instance_of(dict)
    )
    nordic_devicetype = attr.ib(
        default="nrf52832", validator=attr.validators.instance_of(str)
    )
    arm_devicetype = attr.ib(
        default="lpc1519", validator=attr.validators.instance_of(str)
    )
    fixture = attr.ib(default="", validator=attr.validators.instance_of(str))


class Config:

    """Base configuration for RVMN101 and RVMN5x."""

    values = None  # Values instance
    vbatt_set = 12.5
    # Test limits common to all units and test types
    _base_limits = (
        tester.LimitRegExp("BleMac", "^[0-9a-f]{12}$", doc="Valid MAC address"),
    )
    # Initial Test limits common to all units
    _base_limits_initial = _base_limits + (
        tester.LimitDelta("Vbatt", vbatt_set - 0.5, 1.0, doc="Battery input"),
        tester.LimitPercent("3V3", 3.3, 6.0, doc="Internal 3V rail"),
        tester.LimitHigh("HSon", 9.0, doc="HS output on (high)"),
        tester.LimitLow("HSoff", 3.0, doc="All HS outputs off (low)"),
        tester.LimitLow("HBon", 2.0, doc="Reversed HBridge on (low)"),
        tester.LimitHigh("HBoff", 6.0, doc="Reversed HBridge off (high)"),
        tester.LimitLow("LSon", 1.0, doc="LS output on (low)"),
        tester.LimitHigh("LSoff", 9.0, doc="LS output off (high)"),
        tester.LimitBoolean("CANok", True, doc="CAN bus active"),
        tester.LimitBetween("AllInputs", 0, 0xFFFF, doc="Digital inputs"),
    )
    # Final Test limits common to all units
    _base_limits_final = _base_limits + (
        tester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
    )

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.tester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.values = cls._rev_data[rev]
        cls.values.fixture = cls._fixture

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_initial

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final


class RVMN101A(Config):

    """RVMN101A configuration."""

    _fixture = "033550"
    _reversed7to9 = {  # Key: any text, Value: Output index
        "HBRIDGE 1 EXTEND": 0,
        "HBRIDGE 1 RETRACT": 1,
        "HBRIDGE 2 EXTEND": 2,
        "HBRIDGE 2 RETRACT": 3,
        "HBRIDGE 3 EXTEND": 4,
        "HBRIDGE 3 RETRACT": 5,
    }
    _nordic_3_2_7 = "rvmn101a_signed_3.2.7-0-gaa43c0ef_factory_mcuboot.hex"
    _arm_image_1_13 = "rvmn101a_nxp_1.13.bin"
    _arm_image_2_5 = "rvmn101a_nxp_2.5.bin"
    _rev29_values = Values(
        nordic_image=_nordic_3_2_7,
        arm_image=_arm_image_2_5,
        product_rev="29A",
        hardware_rev="22A",
    )
    _rev_data = {
        None: _rev29_values,
        "29": _rev29_values,
        "28": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="28B",
            hardware_rev="22A",
        ),
        "27": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="27C",
            hardware_rev="19A",
        ),
        "26": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="26D",
            hardware_rev="19A",
        ),
        "25": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="25E",
            hardware_rev="19A",
        ),
        "24": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="24E",
            hardware_rev="21A",
        ),
        "23": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="23F",
            hardware_rev="21A",  # '21' in the ECO
        ),
        "22": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="22F",
            hardware_rev="20A",  # Missing in the ECO
        ),
        "21": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="21G",
            hardware_rev="20A",  # '20' in the ECO
        ),
        "20": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="20G",
            hardware_rev="14A",
        ),
        "19": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="19I",
            hardware_rev="13A",
        ),
        "18": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="18H",
            hardware_rev="13A",
        ),
        # Rev 17 No production
        "16": Values(  # Note: ECO had wrong HW rev (15A instead of 12A)
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="16K",
            hardware_rev="15A",
        ),
        # Rev 15 No production
        "14": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="14L",
            hardware_rev="11A",
        ),
        "13": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="13I",
            hardware_rev="11A",
        ),
        "12": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_2_5,
            product_rev="12J",
            hardware_rev="11A",
        ),
        # Rev 11 No production
        "10": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_1_13,
            product_rev="10K",
            hardware_rev="10A",
        ),
        # MA-415: Rev <10 "Diagnose and then discard PCB""
        "9": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_1_13,
            product_rev="09A",
            hardware_rev="08A",
            reversed_outputs=_reversed7to9,
        ),
        "8": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_1_13,
            product_rev="08A",
            hardware_rev="08A",
            reversed_outputs=_reversed7to9,
        ),
        "7": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_1_13,
            product_rev="07A",
            hardware_rev="07A",
            reversed_outputs=_reversed7to9,
        ),
        "6": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_arm_image_1_13,
            product_rev="06A",
            hardware_rev="06A",
        ),
        # Rev 1-5 were Engineering protoype builds
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.tester.UUT instance

        """
        super()._configure(uut)
        if uut and uut.lot.number in (  # PC-30067
            "A222304",
            "A222402",
            "A222706",
            "A222804",
        ):
            cls.product_rev = "24A"

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type in ("ATE4", "ATE5") else -85
        return cls._base_limits_final + (
            tester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
        )


class RVMN101B(Config):

    """RVMN101B configuration."""

    _fixture = "032871"
    _nordic_2_5_8 = "rvmn101b_signed_2.5.8-0-gaa43c0ef_factory_mcuboot.hex"
    _arm_image_3_0 = "rvmn101b_nxp_3.0.bin"  # 035879 Rev ≥ 14
    _arm_image_1_9 = "rvmn101b_nxp_1.9.bin"  # 033092 Rev ≤ 13
    _rev21_values = Values(
        nordic_image=_nordic_2_5_8,
        arm_image=_arm_image_3_0,
        product_rev="21A",
        hardware_rev="08B",
    )
    _rev_data = {
        None: _rev21_values,
        "21": _rev21_values,
        "20": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="20B",
            hardware_rev="08B",
        ),
        "19": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="19C",
            hardware_rev="08B",
        ),
        "18": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="18D",
            hardware_rev="18A",  # This looks wrong, but is per the ECO
        ),
        "17": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="17D",
            hardware_rev="08B",
        ),
        "16": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="16E",
            hardware_rev="08B",
        ),
        "15": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="15F",
            hardware_rev="8B",
        ),
        "14": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_3_0,
            product_rev="14H",
            hardware_rev="8A",
        ),
        "13": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="13I",
            hardware_rev="8A",
        ),
        "12": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="12J",
            hardware_rev="6A",
        ),
        "11": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="11J",
            hardware_rev="6A",
        ),
        "10": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="10K",
            hardware_rev="6A",
        ),
        "9": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="09K",
            hardware_rev="6A",
        ),
        "8": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="08L",
            hardware_rev="6A",
        ),
        "7": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="07K",
            hardware_rev="6A",
        ),
        "6": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="06L",
            hardware_rev="6A",
        ),
        "5": Values(
            nordic_image=_nordic_2_5_8,
            arm_image=_arm_image_1_9,
            product_rev="05K",
            hardware_rev="6A",
        ),
        # Rev 1-4 were Engineering protoype builds
    }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        # 3dB below the -A version
        rssi = -73 if share.config.System.tester_type in ("ATE4", "ATE5") else -88
        return cls._base_limits_final + (
            tester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
        )


class RVMN101C(Config):

    """RVMN101C configuration."""

    _fixture = "033550"
    _sonic_1_0_6 = "rvmn101c_signed_1.0.6-0-gd721feb0_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev4_values = Values(
        nordic_image=_sonic_1_0_6,
        arm_image=_arm_image_3_0_1,
        product_rev="04A",
        hardware_rev="04A",
        nordic_devicetype="nrf52840",
    )
    _rev_data = {
        None: _rev4_values,
        "4": _rev4_values,
        "3": Values(
            nordic_image=_sonic_1_0_6,
            arm_image=_arm_image_3_0_1,
            product_rev="03D",
            hardware_rev="03A",
            nordic_devicetype="nrf52840",
        ),
    }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type in ("ATE4", "ATE5") else -85
        return cls._base_limits_final + (
            tester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
        )


class RVMN5x(Config):

    """RVMN5x configuration."""

    _fixture = "034861"
    _nordic_3_2_7 = "rvmn5x_signed_3.2.7-0-gaa43c0ef_factory_mcuboot.hex"
    _nxp_image_2_3 = "rvmn5x_nxp_2.3.bin"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev19_values = Values(
        nordic_image=_nordic_3_2_7,
        arm_image=_ra2_image_0_3_6,
        product_rev="19A",
        hardware_rev="12A",
        arm_devicetype="r7fa2l1a9",
    )
    _rev_data = {
        None: _rev19_values,
        "19": _rev19_values,
        "18": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="18B",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "17": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="17C",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "16": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="16D",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "15": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="15E",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "14": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="14E",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "13": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_ra2_image_0_3_6,
            product_rev="13F",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "12": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="12F",
            hardware_rev="08A",
        ),
        "10": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="10G",
            hardware_rev="08A",
        ),
        "9": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="09G",
            hardware_rev="07A",
        ),
        "8": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="08I",
            hardware_rev="05A",
        ),
        "7": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="07H",
            hardware_rev="05A",
        ),
        "6": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="06J",
            hardware_rev="05A",
        ),
        "5": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="05L",
            hardware_rev="05A",
        ),
        "4": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="04J",
            hardware_rev="04A",
        ),
        "3": Values(
            nordic_image=_nordic_3_2_7,
            arm_image=_nxp_image_2_3,
            product_rev="03M",
            hardware_rev="03A",
        ),
        # Rev 1-2 were Engineering protoype builds
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.tester.UUT instance

        """
        super()._configure(uut)
        if uut and uut.lot.number in (  # PC-30068 for RVMN50
            "A222306",
            "A222708",
            "A222806",
            "A222917",
            "A223016",
        ):
            cls.product_rev = "14A"

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type in ("ATE4", "ATE5") else -85
        return cls._base_limits_final + (
            tester.LimitHigh("ScanRSSI", rssi, doc="Strong BLE signal"),
        )
