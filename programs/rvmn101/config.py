#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMNx Configuration."""

import logging

from attrs import define, field, validators
import tester

import share


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "101A": RVMN101A,
        "101B": RVMN101B,
        "101C": RVMN101C,
        "200A": RVMN200A,
        "50": RVMN5x,
        "55": RVMN5x,
        "60": RVMN6x,
        "65": RVMN6x,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


@define
class Values:

    """Adjustable configuration data values.

    These values get set per Product type & revision

    """

    nordic_image = field(validator=validators.instance_of(str))
    arm_image = field(validator=validators.instance_of(str))
    product_rev = field(validator=validators.instance_of(str))
    hardware_rev = field()
    reversed_outputs = field(
        factory=dict, validator=validators.instance_of(dict)
    )
    nordic_devicetype = field(
        default="nrf52832", validator=validators.instance_of(str)
    )
    arm_devicetype = field(
        default="lpc1519", validator=validators.instance_of(str)
    )
    fixture = field(default="", validator=validators.instance_of(str))


class Config:

    """Base configuration for RVMNx."""

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
        tester.LimitRegExp("Serial", "", doc="Correct serial number"),
        tester.LimitRegExp("ProdRev", "", doc="Correct product revision"),
        tester.LimitRegExp("HardRev", "", doc="Correct hardware revision"),
    )
    # Final Test limits common to all units
    _base_limits_final = _base_limits + (
        tester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
    )

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

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
    _nordic_3_4_2 = "rvmn101a_signed_3.4.2-0-g5f0b6377_factory_mcuboot.hex"
    _arm_image_1_13 = "rvmn101a_nxp_1.13.bin"
    _arm_image_2_5 = "rvmn101a_nxp_2.5.bin"
    _rev31_values = Values(
        nordic_image=_nordic_3_4_2,
        arm_image=_arm_image_2_5,
        product_rev="31A",
        hardware_rev="22A",
    )
    _rev_data = {
        None: _rev31_values,
        "31": _rev31_values,
        "30": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="30B",
            hardware_rev="22A",
        ),
        "29": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="29C",
            hardware_rev="22A",
        ),
        "28": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="28D",
            hardware_rev="22A",
        ),
        "27": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="27E",
            hardware_rev="19A",
        ),
        "26": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="26F",
            hardware_rev="19A",
        ),
        "25": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="25G",
            hardware_rev="19A",
        ),
        "24": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="24G",
            hardware_rev="21A",
        ),
        "23": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="23H",
            hardware_rev="21A",  # '21' in the ECO
        ),
        "22": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="22H",
            hardware_rev="20A",  # Missing in the ECO
        ),
        "21": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="21H",
            hardware_rev="20A",  # '20' in the ECO
        ),
        "20": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="20I",
            hardware_rev="14A",
        ),
        "19": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="19K",
            hardware_rev="13A",
        ),
        "18": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="18J",
            hardware_rev="13A",
        ),
        # Rev 17 No production
        "16": Values(  # Note: ECO had wrong HW rev (15A instead of 12A)
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="16M",
            hardware_rev="15A",
        ),
        # Rev 15 No production
        "14": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="14N",
            hardware_rev="11A",
        ),
        "13": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="13K",
            hardware_rev="11A",
        ),
        "12": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_2_5,
            product_rev="12L",
            hardware_rev="11A",
        ),
        # Rev 11 No production
        "10": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_1_13,
            product_rev="10M",
            hardware_rev="10A",
        ),
        # MA-415: Rev <10 "Diagnose and then discard PCB""
        "9": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_1_13,
            product_rev="09A",
            hardware_rev="08A",
            reversed_outputs=_reversed7to9,
        ),
        "8": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_1_13,
            product_rev="08A",
            hardware_rev="08A",
            reversed_outputs=_reversed7to9,
        ),
        "7": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_1_13,
            product_rev="07A",
            hardware_rev="07A",
            reversed_outputs=_reversed7to9,
        ),
        "6": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_arm_image_1_13,
            product_rev="06A",
            hardware_rev="06A",
        ),
        # Rev 1-5 were Engineering protoype builds
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

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
    _nordic_2_6_3 = "rvmn101b_signed_2.6.3-0-g129a5c96_factory_mcuboot.hex"
    _arm_image_3_1 = "rvmn101b_nxp_3.1.bin"  # 039578 Rev ≥ 22
    _arm_image_3_0 = "rvmn101b_nxp_3.0.bin"  # 035879 Rev ≥ 14
    _arm_image_1_9 = "rvmn101b_nxp_1.9.bin"  # 033092 Rev ≤ 13
    _rev22_values = Values(
        nordic_image=_nordic_2_6_3,
        arm_image=_arm_image_3_1,
        product_rev="22A",
        hardware_rev="13A",
    )
    _rev_data = {
        None: _rev22_values,
        "22": _rev22_values,
        "21": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="21B",
            hardware_rev="08B",
        ),
        "20": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="20D",
            hardware_rev="08B",
        ),
        "19": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="19D",
            hardware_rev="08B",
        ),
        "18": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="18E",
            hardware_rev="18A",  # This looks wrong, but is per the ECO
        ),
        "17": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="17E",
            hardware_rev="08B",
        ),
        "16": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="16F",
            hardware_rev="08B",
        ),
        "15": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="15G",
            hardware_rev="8B",
        ),
        "14": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_0,
            product_rev="14I",
            hardware_rev="8A",
        ),
        "13": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="13J",
            hardware_rev="8A",
        ),
        "12": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="12K",
            hardware_rev="6A",
        ),
        "11": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="11K",
            hardware_rev="6A",
        ),
        "10": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="10L",
            hardware_rev="6A",
        ),
        "9": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="09L",
            hardware_rev="6A",
        ),
        "8": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="08M",
            hardware_rev="6A",
        ),
        "7": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="07L",
            hardware_rev="6A",
        ),
        "6": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="06M",
            hardware_rev="6A",
        ),
        "5": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_1_9,
            product_rev="05L",
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
    _sonic_1_0_7 = "rvmn101c_signed_1.0.7-0-g0d768132_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev5_values = Values(
        nordic_image=_sonic_1_0_7,
        arm_image=_arm_image_3_0_1,
        product_rev="05A",
        hardware_rev="04A",
        nordic_devicetype="nrf52840",
    )
    _rev_data = {
        None: _rev5_values,
        "5": _rev5_values,
        "4": Values(
            nordic_image=_sonic_1_0_7,
            arm_image=_arm_image_3_0_1,
            product_rev="04B",
            hardware_rev="04A",
            nordic_devicetype="nrf52840",
        ),
        "3": Values(
            nordic_image=_sonic_1_0_7,
            arm_image=_arm_image_3_0_1,
            product_rev="03E",
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


class RVMN200A(Config):

    """RVMN200A configuration."""

    _fixture = "033550"
    _sonic_4_2_0 = "rvmn200a_signed_4.2.0-0-g0734a4ac_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev1_values = Values(
        nordic_image=_sonic_4_2_0,
        arm_image=_arm_image_3_0_1,
        product_rev="01A",
        hardware_rev="01A",
        nordic_devicetype="nrf52840",
    )
    _rev_data = {
        None: _rev1_values,
        "1": _rev1_values,
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
    _nordic_3_4_2 = "rvmn5x_signed_3.4.2-0-g5f0b6377_factory_mcuboot.hex"
    _nxp_image_2_3 = "rvmn5x_nxp_2.3.bin"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev21_values = Values(
        nordic_image=_nordic_3_4_2,
        arm_image=_ra2_image_0_3_6,
        product_rev="21A",
        hardware_rev="12A",
        arm_devicetype="r7fa2l1a9",
    )
    _rev_data = {
        None: _rev21_values,
        "21": _rev21_values,
        "20": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="20B",
            hardware_rev="12A",
            arm_devicetype="r7fa2l1a9",
        ),
        "19": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="19C",
            hardware_rev="12A",
            arm_devicetype="r7fa2l1a9",
        ),
        "18": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="18D",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "17": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="17E",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "16": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="16F",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "15": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="15G",
            hardware_rev="11A",
            arm_devicetype="r7fa2l1a9",
        ),
        "14": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="14G",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "13": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_ra2_image_0_3_6,
            product_rev="13H",
            hardware_rev="10A",
            arm_devicetype="r7fa2l1a9",
        ),
        "12": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="12H",
            hardware_rev="08A",
        ),
        "10": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="10H",
            hardware_rev="08A",
        ),
        "9": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="09I",
            hardware_rev="07A",
        ),
        "8": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="08J",
            hardware_rev="05A",
        ),
        "7": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="07J",
            hardware_rev="05A",
        ),
        "6": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="06L",
            hardware_rev="05A",
        ),
        "5": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="05N",
            hardware_rev="05A",
        ),
        "4": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="04L",
            hardware_rev="04A",
        ),
        "3": Values(
            nordic_image=_nordic_3_4_2,
            arm_image=_nxp_image_2_3,
            product_rev="03O",
            hardware_rev="03A",
        ),
        # Rev 1-2 were Engineering protoype builds
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

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


class RVMN6x(Config):

    """RVMN6x configuration."""

    _fixture = "034861"
    _nordic_4_2_0 = "rvmn6x_signed_4.2.0-0-g0734a4ac_factory_mcuboot.hex"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev1_values = Values(
        nordic_image=_nordic_4_2_0,
        arm_image=_ra2_image_0_3_6,
        product_rev="01A",
        hardware_rev="01A",
        arm_devicetype="r7fa2l1a9",
        nordic_devicetype="nrf52840",
    )
    _rev_data = {
        None: _rev1_values,
        "1": _rev1_values,
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
