#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import attr


@attr.s
class _Values():

    """Configuration data values."""

    product_rev = attr.ib(validator=attr.validators.instance_of(str))
    hardware_rev = attr.ib(validator=attr.validators.instance_of(str))
    sw_arm_image = attr.ib(validator=attr.validators.instance_of(str))
    sw_nrf_image = attr.ib(validator=attr.validators.instance_of(str))
    is_smartlink = attr.ib(validator=attr.validators.instance_of(bool))
    banner_lines = attr.ib(validator=attr.validators.instance_of(int))


class Config():

    """Configuration options."""

    _hw_rev = '02B'
    _arm_image = 'nxp_v0.1.0.bin'
    _options = {
        'B': _Values(           # BLExtender
            product_rev = '01A',
            hardware_rev = _hw_rev,
            sw_arm_image = _arm_image,  # no NXP in this product
            sw_nrf_image = (
                'blextender_v1.3.0-0-g6c6b4fa-signed-mcuboot-factory.hex'),
            is_smartlink = False,
            banner_lines = 11
            ),
        'S': _Values(           # Smartlink201
            product_rev = '02A',
            hardware_rev = _hw_rev,
            sw_arm_image = _arm_image,
            sw_nrf_image = (
                'smartlink_signed_1.0.0-0-gacbb530_factory_mcuboot.hex'),
            is_smartlink = True,
            banner_lines = 12
            ),
        }

    @classmethod
    def get(cls, parameter, uut):
        """Retrieve product config data.

        @param parameter Product type selector
        @param uut Unit under test instance_of
        @return _Values instance

        """
        return cls._options[parameter]
