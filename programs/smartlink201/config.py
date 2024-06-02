#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import logging

from attrs import define, field, validators


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "B": BLExtender,
        "S": SmartLink201,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


@define
class _Values:
    """Configuration data values."""

    product_rev = field(validator=validators.instance_of(str))
    hardware_rev = field(validator=validators.instance_of(str))
    sw_nrf_image = field(validator=validators.instance_of(str))
    sw_arm_image = field(
        default="nxp_v0.1.0.bin", validator=validators.instance_of(str)
    )
    is_smartlink = field(default=True, validator=validators.instance_of(bool))


class _Config:
    """Configuration options."""

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.sw_arm_image = values.sw_arm_image
        cls.sw_nrf_image = values.sw_nrf_image
        cls.is_smartlink = values.is_smartlink


class BLExtender(_Config):
    """BLExtender config."""

    _hw_rev = "02B"
    _sw_nrf_image = "blextender_v1.3.1-0-g88992a0_signed_mcuboot_factory.hex"
    _rev2_values = _Values(
        product_rev="02A",
        hardware_rev=_hw_rev,
        sw_nrf_image=_sw_nrf_image,
        is_smartlink=False,
    )
    _rev_data = {
        None: _rev2_values,
        "2": _rev2_values,
        "1": _Values(
            product_rev="01B",
            hardware_rev=_hw_rev,
            sw_nrf_image=_sw_nrf_image,  # MA-451
            is_smartlink=False,
        ),
    }


class SmartLink201(_Config):
    """SmartLink201 config."""

    _sw_nrf_image = "smartlink_signed_1.2.1-0-g744e6db_factory_mcuboot.hex"
    _rev4_values = _Values(
        product_rev="04A",
        hardware_rev="03A",
        sw_nrf_image=_sw_nrf_image,
    )
    _rev_data = {
        None: _rev4_values,
        "4": _rev4_values,
        "3": _Values(
            product_rev="03B",
            hardware_rev="02B",
            sw_nrf_image=_sw_nrf_image,  # MA-401
        ),
        "2": _Values(
            product_rev="02B",
            hardware_rev="02B",
            sw_nrf_image=_sw_nrf_image,  # MA-401
        ),
        # No Rev 1 production
    }
