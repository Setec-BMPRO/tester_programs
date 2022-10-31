#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import logging

import attr


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut setec.UUT instance
    @return configuration class

    """
    config = {
        "B": BLExtender,
        "S": SmartLink201,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


@attr.define
class _Values:

    """Configuration data values."""

    product_rev = attr.field(validator=attr.validators.instance_of(str))
    hardware_rev = attr.field(validator=attr.validators.instance_of(str))
    sw_arm_image = attr.field(validator=attr.validators.instance_of(str))
    sw_nrf_image = attr.field(validator=attr.validators.instance_of(str))
    sw_nrf_projectfile = attr.field(validator=attr.validators.instance_of(str))
    is_smartlink = attr.field(validator=attr.validators.instance_of(bool))


class _Config:

    """Configuration options."""

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.sw_arm_image = values.sw_arm_image
        cls.sw_nrf_image = values.sw_nrf_image
        cls.sw_nrf_projectfile = values.sw_nrf_projectfile
        cls.is_smartlink = values.is_smartlink


class BLExtender(_Config):

    """BLExtender config."""

    _arm_image = "nxp_v0.1.0.bin"
    _hw_rev = "02B"
    _rev1_values = _Values(
        product_rev="01A",
        hardware_rev=_hw_rev,
        sw_arm_image=_arm_image,  # no NXP in this product
        sw_nrf_image=("blextender_v1.3.0-0-g6c6b4fa-signed-mcuboot-factory.hex"),
        sw_nrf_projectfile="nrf52.jflash",
        is_smartlink=False,
    )
    _rev_data = {
        None: _rev1_values,
        "1": _rev1_values,
    }


class SmartLink201(_Config):

    """SmartLink201 config."""

    _arm_image = "nxp_v0.1.0.bin"
    _sw_nrf_image = "smartlink_signed_1.2.1-0-g744e6db_factory_mcuboot.hex"
    _sw_nrf_projectfile = "nrf52.jflash"
    _rev4_values = _Values(
        product_rev="04A",
        hardware_rev="03A",
        sw_arm_image=_arm_image,
        sw_nrf_image=_sw_nrf_image,
        sw_nrf_projectfile=_sw_nrf_projectfile,
        is_smartlink=True,
    )
    _rev_data = {
        None: _rev4_values,
        "4": _rev4_values,
        "3": _Values(
            product_rev="03B",
            hardware_rev="02B",
            sw_arm_image=_arm_image,
            sw_nrf_image=_sw_nrf_image,  # MA-401
            sw_nrf_projectfile=_sw_nrf_projectfile,
            is_smartlink=True,
        ),
        "2": _Values(
            product_rev="02B",
            hardware_rev="02B",
            sw_arm_image=_arm_image,
            sw_nrf_image=_sw_nrf_image,  # MA-401
            sw_nrf_projectfile=_sw_nrf_projectfile,
            is_smartlink=True,
        ),
        # No Rev 1 production
    }
