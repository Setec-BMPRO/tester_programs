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
class _Values:

    """Adjustable configuration data values."""

    nordic_image = attr.ib(validator=attr.validators.instance_of(str))
    arm_image = attr.ib(validator=attr.validators.instance_of(str))
    product_rev = attr.ib(validator=attr.validators.instance_of(str))
    hardware_rev = attr.ib()
    reversed_output_dict = attr.ib(
        default={}, validator=attr.validators.instance_of(dict)
    )
    nordic_devicetype = attr.ib(
        default="nrf52832", validator=attr.validators.instance_of(str)
    )
    arm_devicetype = attr.ib(
        default="lpc1519", validator=attr.validators.instance_of(str)
    )


class Config:

    """Base configuration for RVMN101 and RVMN5x."""

    # These values get set per Product type & revision
    nordic_devicetype = None
    nordic_image = None
    arm_devicetype = None
    arm_image = None
    product_rev = None
    hardware_rev = None
    reversed_output_dict = None
    # General parameters used in testing the units
    #  Injected voltages
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
        values = cls._rev_data[rev]
        cls.nordic_devicetype = values.nordic_devicetype
        cls.nordic_image = values.nordic_image
        cls.arm_devicetype = values.arm_devicetype
        cls.arm_image = values.arm_image
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.reversed_output_dict = values.reversed_output_dict

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

    # Initial Test parameters
    fixture = "033550"
    # Reversed outputs exist on Rev 7,8,9 units
    _reversed7to9 = {  # Key: any text, Value: Output index
        "HBRIDGE 1 EXTEND": 0,
        "HBRIDGE 1 RETRACT": 1,
        "HBRIDGE 2 EXTEND": 2,
        "HBRIDGE 2 RETRACT": 3,
        "HBRIDGE 3 EXTEND": 4,
        "HBRIDGE 3 RETRACT": 5,
    }
    # Software versions
    _nordic_3_1_5 = "rvmn101a_signed_3.1.5-0-g42007340_factory_mcuboot.hex"
    _arm_image_1_13 = "rvmn101a_nxp_1.13.bin"
    _arm_image_2_5 = "rvmn101a_nxp_2.5.bin"
    _rev28_values = _Values(
        nordic_image=_nordic_3_1_5,
        arm_image=_arm_image_2_5,
        product_rev="28A",
        hardware_rev="22A",
    )
    _rev_data = {
        None: _rev28_values,
        "28": _rev28_values,
        "27": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="27B",
            hardware_rev="19A",
        ),
        "26": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="26C",
            hardware_rev="19A",
        ),
        "25": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="25D",
            hardware_rev="19A",
        ),
        "24": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="24D",
            hardware_rev="21A",
        ),
        "23": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="23E",
            hardware_rev="21A",  # '21' in the ECO
        ),
        "22": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="22E",
            hardware_rev="20A",  # Missing in the ECO
        ),
        "21": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="21F",
            hardware_rev="20A",  # '20' in the ECO
        ),
        "20": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="20F",
            hardware_rev="14A",
        ),
        "19": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="19H",
            hardware_rev="13A",
        ),
        "18": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="18G",
            hardware_rev="13A",
        ),
        # Rev 17 No production
        "16": _Values(  # Note: ECO had wrong HW rev (15A instead of 12A)
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="16J",
            hardware_rev="15A",
        ),
        # Rev 15 No production
        "14": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="14K",
            hardware_rev="11A",
        ),
        "13": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="13H",
            hardware_rev="11A",
        ),
        "12": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_2_5,
            product_rev="12I",
            hardware_rev="11A",
        ),
        # Rev 11 No production
        "10": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_1_13,
            product_rev="10J",
            hardware_rev="10A",
        ),
        # MA-415: Rev <10 "Diagnose and then discard PCB""
        "9": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_1_13,
            product_rev="09A",
            hardware_rev="08A",
            reversed_output_dict=_reversed7to9,
        ),
        "8": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_1_13,
            product_rev="08A",
            hardware_rev="08A",
            reversed_output_dict=_reversed7to9,
        ),
        "7": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_arm_image_1_13,
            product_rev="07A",
            hardware_rev="07A",
            reversed_output_dict=_reversed7to9,
        ),
        "6": _Values(
            nordic_image=_nordic_3_1_5,
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
        # PC-30067
        if uut and uut.lot.number in ("A222304", "A222402", "A222706", "A222804"):
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

    # Initial Test parameters
    fixture = "032871"
    # Software versions
    _nordic_2_4_6 = "rvmn101b_signed_2.4.6-0-g5807fc70_factory_mcuboot.hex"  # 038685
    _arm_image_3_0 = "rvmn101b_nxp_3.0.bin"  # 035879 Rev ≥ 14
    _arm_image_1_9 = "rvmn101b_nxp_1.9.bin"  # 033092 Rev ≤ 13
    _rev20_values = _Values(
        nordic_image=_nordic_2_4_6,
        arm_image=_arm_image_3_0,
        product_rev="20A",
        hardware_rev="18A",
    )
    _rev_data = {
        None: _rev20_values,
        "20": _rev20_values,
        "19": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="19B",
            hardware_rev="08B",
        ),
        "18": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="18C",
            hardware_rev="18A",
        ),
        "17": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="17C",
            hardware_rev="08B",
        ),
        "16": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="16D",
            hardware_rev="08B",
        ),
        "15": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="15E",
            hardware_rev="8B",
        ),
        "14": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_3_0,
            product_rev="14G",
            hardware_rev="8A",
        ),
        "13": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="13H",
            hardware_rev="8A",
        ),
        "12": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="12I",
            hardware_rev="6A",
        ),
        "11": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="11I",
            hardware_rev="6A",
        ),
        "10": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="10J",
            hardware_rev="6A",
        ),
        "9": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="09J",
            hardware_rev="6A",
        ),
        "8": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="08K",
            hardware_rev="6A",
        ),
        "7": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="07J",
            hardware_rev="6A",
        ),
        "6": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="06K",
            hardware_rev="6A",
        ),
        "5": _Values(
            nordic_image=_nordic_2_4_6,
            arm_image=_arm_image_1_9,
            product_rev="05J",
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

    # Initial Test parameters
    fixture = "033550"
    # Software versions
    _sonic_1_0_4 = "rvmn101c_signed_1.0.4-0-g7937e578_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev3_values = _Values(
        nordic_image=_sonic_1_0_4,
        arm_image=_arm_image_3_0_1,
        product_rev="03B",
        hardware_rev="02A",
        nordic_devicetype = "nrf52840"
    )
    _rev_data = {
        None: _rev3_values,
        "3": _rev3_values,
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

    # Initial Test parameters
    fixture = "034861"
    # Software versions
    _nordic_3_1_5 = "rvmn5x_signed_3.1.5-0-g42007340_factory_mcuboot.hex"
    _nxp_image_2_3 = "rvmn5x_nxp_2.3.bin"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev18_values = _Values(
        nordic_image=_nordic_3_1_5,
        arm_image=_ra2_image_0_3_6,
        product_rev="18A",
        hardware_rev="11A",
        arm_devicetype="r7fa2l1a9",
    )
    _rev_data = {
        None: _rev18_values,
        "18": _rev18_values,
        "17": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_ra2_image_0_3_6,
            product_rev="17B",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "16": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_ra2_image_0_3_6,
            product_rev="16C",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "15": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_ra2_image_0_3_6,
            product_rev="15D",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "14": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_ra2_image_0_3_6,
            product_rev="14D",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "13": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_ra2_image_0_3_6,
            product_rev="13E",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "12": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="12E",
            hardware_rev="08A",
        ),
        "10": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="10F",
            hardware_rev="08A",
        ),
        "9": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="09F",
            hardware_rev="07A",
        ),
        "8": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="08H",
            hardware_rev="05A",
        ),
        "7": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="07G",
            hardware_rev="05A",
        ),
        "6": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="06I",
            hardware_rev="05A",
        ),
        "5": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="05K",
            hardware_rev="05A",
        ),
        "4": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="04I",
            hardware_rev="04A",
        ),
        "3": _Values(
            nordic_image=_nordic_3_1_5,
            arm_image=_nxp_image_2_3,
            product_rev="03L",
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
        # PC-30068 for RVMN50
        if uut and uut.lot.number in (
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
