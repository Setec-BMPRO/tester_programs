#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMNx Configuration."""

import logging

from attrs import define, field, validators
import libtester

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
        "300A": RVMN300x,
        "300C": RVMN300x,
        "301C": RVMN300x,
        "50": RVMN5x,
        "55": RVMN5x,
        "60": RVMN6x,
        "65": RVMN6x,
        "70": RVMN7x,
        "75": RVMN7x,
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
    hardware_rev = field(validator=validators.instance_of(str))
    reversed_outputs = field(factory=dict, validator=validators.instance_of(dict))
    nordic_devicetype = field(default="nrf52832", validator=validators.instance_of(str))
    arm_devicetype = field(default="lpc1519", validator=validators.instance_of(str))
    # Confirmed problems with: RVMN101B, RVMN200A, RVMN6x
    boot_delay = field(default=4, converter=float)


class Config:
    """Base configuration for RVMNx."""

    values = None  # Values instance
    vbatt_set = 12.5
    # Test limits common to all units and test types
    _base_limits = (
        libtester.LimitRegExp("BleMac", share.MAC.regex, doc="Valid MAC address"),
    )
    # Initial Test limits common to all units
    _base_limits_initial = _base_limits + (
        libtester.LimitDelta("Vbatt", vbatt_set - 0.5, 1.0, doc="Battery input"),
        libtester.LimitPercent("3V3", 3.3, 6.0, doc="Internal 3V rail"),
        libtester.LimitHigh("HSon", 9.0, doc="HS output on (high)"),
        libtester.LimitLow("HSoff", 3.0, doc="All HS outputs off (low)"),
        libtester.LimitLow("HBon", 2.0, doc="Reversed HBridge on (low)"),
        libtester.LimitHigh("HBoff", 6.0, doc="Reversed HBridge off (high)"),
        libtester.LimitLow("LSon", 1.0, doc="LS output on (low)"),
        libtester.LimitHigh("LSoff", 9.0, doc="LS output off (high)"),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
        libtester.LimitBetween("AllInputs", 0, 0xFFFF, doc="Digital inputs"),
        libtester.LimitRegExp("Serial", "None", doc="Correct serial number"),
        libtester.LimitRegExp("ProdRev", "None", doc="Correct product revision"),
        libtester.LimitRegExp("HardRev", "None", doc="Correct hardware revision"),
    )
    # Final Test limits common to all units
    _base_limits_final = _base_limits

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.values = cls._rev_data[rev]

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


class RVMN101B(Config):
    """RVMN101B configuration."""

    _nordic_2_6_3 = "rvmn101b_signed_2.6.3-0-g129a5c96_factory_mcuboot.hex"
    _arm_image_3_1 = "rvmn101b_nxp_3.1.bin"  # 039578 Rev ≥ 22
    _arm_image_3_0 = "rvmn101b_nxp_3.0.bin"  # 035879 Rev ≥ 14
    _arm_image_1_9 = "rvmn101b_nxp_1.9.bin"  # 033092 Rev ≤ 13
    _rev23_values = Values(
        nordic_image=_nordic_2_6_3,
        arm_image=_arm_image_3_1,
        product_rev="23A",
        hardware_rev="14A",
    )
    _rev_data = {
        None: _rev23_values,
        "23": _rev23_values,
        "22": Values(
            nordic_image=_nordic_2_6_3,
            arm_image=_arm_image_3_1,
            product_rev="22A",
            hardware_rev="13A",
        ),
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


class RVMN101C(Config):
    """RVMN101C configuration."""

    _sonic_1_1_0 = "rvmn101c_signed_1.1.0-0-gc33c86fd_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev6_values = Values(
        nordic_image=_sonic_1_1_0,
        arm_image=_arm_image_3_0_1,
        product_rev="06A",
        hardware_rev="04A",
        nordic_devicetype="nrf52840",
    )
    _rev_data = {
        None: _rev6_values,
        "6": _rev6_values,
        "5": Values(
            nordic_image=_sonic_1_1_0,
            arm_image=_arm_image_3_0_1,
            product_rev="05B",
            hardware_rev="04A",
            nordic_devicetype="nrf52840",
        ),
        "4": Values(
            nordic_image=_sonic_1_1_0,
            arm_image=_arm_image_3_0_1,
            product_rev="04C",
            hardware_rev="04A",
            nordic_devicetype="nrf52840",
        ),
        "3": Values(
            nordic_image=_sonic_1_1_0,
            arm_image=_arm_image_3_0_1,
            product_rev="03F",
            hardware_rev="03A",
            nordic_devicetype="nrf52840",
        ),
    }


class RVMN200A(Config):
    """RVMN200A configuration."""

    _sonic_4_2_1 = "rvmn200a_signed_4.2.1-0-g51e17e2c_factory_mcuboot.hex"
    _arm_image_3_0_1 = "rvmn101c_nxp_3.0.1-0-gc609bee.bin"
    _rev2_values = Values(
        nordic_image=_sonic_4_2_1,
        arm_image=_arm_image_3_0_1,
        product_rev="02A",
        hardware_rev="02A",
        nordic_devicetype="nrf52840",
        # FIXME: Console prompt appears before it is ready to accept commands
        # 2s gives a 1 in 5 branding failure rate
        boot_delay=4,
    )
    _rev_data = {
        None: _rev2_values,
        "3": _rev2_values,
        "2": _rev2_values,
        "1": Values(
            nordic_image=_sonic_4_2_1,
            arm_image=_arm_image_3_0_1,
            product_rev="01B",
            hardware_rev="01A",
            nordic_devicetype="nrf52840",
            boot_delay=4,
        ),
    }


class RVMN300x(Config):
    """RVMN300x configuration."""

    _sonic_5_2_3 = "jayco_rvmn300_signed_5.2.3-0-gd0149202_factory_mcuboot.hex"
    _arm_image_4_0_1 = "rvmn300_nxp_v4.0.1_61d85c8.bin" # Conditionally released FW - Full testing yet to be done. MP - 13/02/2024
    _rev3_values = Values(    
        nordic_image=_sonic_5_2_3,
        arm_image=_arm_image_4_0_1,
        product_rev="03A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
        hardware_rev="02A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
        nordic_devicetype="nrf52840",
        # FIXME: Console prompt appears before it is ready to accept commands
        # 2s gives a 1 in 5 branding failure rate
        boot_delay=4,
    )
    _rev_data = {
        None: _rev3_values,
        "3": _rev3_values,
        "2": Values(
            nordic_image=_sonic_5_2_3,
            arm_image=_arm_image_4_0_1,
            product_rev="02A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
            hardware_rev="01A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
            nordic_devicetype="nrf52840",
            boot_delay=4,
        ),
        "1": Values(
            nordic_image=_sonic_5_2_3,
            arm_image=_arm_image_4_0_1,
            product_rev="01A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
            hardware_rev="01A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
            nordic_devicetype="nrf52840",
            boot_delay=4,
        ),
       
    }

class RVMN5x(Config):
    """RVMN5x configuration."""

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


class RVMN6x(Config):
    """RVMN6x configuration."""

    _nordic_4_2_1 = "rvmn6x_signed_4.2.1-0-g51e17e2c_factory_mcuboot.hex"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev2_values = Values(
        nordic_image=_nordic_4_2_1,
        arm_image=_ra2_image_0_3_6,
        product_rev="02A",
        hardware_rev="01A",
        arm_devicetype="r7fa2l1a9",
        nordic_devicetype="nrf52840",
        # FIXME: Console prompt appears before it is ready to accept commands
        # 2s gives a 1 in 5 branding failure rate
        boot_delay=4,
    )
    _rev_data = {
        None: _rev2_values,
        "2": _rev2_values,
        "1": Values(
            nordic_image=_nordic_4_2_1,
            arm_image=_ra2_image_0_3_6,
            product_rev="01B",
            hardware_rev="01A",
            arm_devicetype="r7fa2l1a9",
            nordic_devicetype="nrf52840",
            boot_delay=4,
        ),
    }


class RVMN7x(Config):
    """RVMN7x configuration."""

    _sonic_5_2_3 = "jayco_rvmn7x_signed_5.2.3-0-gd0149202_factory_mcuboot.hex"
    _ra2_image_0_3_6 = "rvmn5x_ra2_v0.3.6-0-g34e425b.hex"
    _rev3_values = Values(
        nordic_image=_sonic_5_2_3,
        arm_image=_ra2_image_0_3_6,
        product_rev="03A", # TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
        hardware_rev="02A",# TODO: Update from F:\PLM\PRODUCTS\RVMN7x\08_Change Management\10_Engineering Change Order\_Released
        arm_devicetype="r7fa2l1a9",
        # FIXME: Console prompt appears before it is ready to accept commands
        # 2s gives a 1 in 5 branding failure rate
        boot_delay=6,
    )
    _rev_data = {
        None: _rev3_values,
        "3": _rev3_values,
        "2": Values(
            nordic_image=_sonic_5_2_3,
            arm_image=_ra2_image_0_3_6,
            product_rev="02A", 
            hardware_rev="01A",
            arm_devicetype="r7fa2l1a9",
            nordic_devicetype="nrf52840",
            boot_delay=6,
        ),
        "1": Values(
            nordic_image=_sonic_5_2_3,
            arm_image=_ra2_image_0_3_6,
            product_rev="01A", 
            hardware_rev="01A",
            arm_devicetype="r7fa2l1a9",
            nordic_devicetype="nrf52840",
            boot_delay=6,
        ),
    }
