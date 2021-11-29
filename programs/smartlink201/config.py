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
        'B': BLExtender,
        'S': SmartLink201,
        }[parameter]
    config._configure(uut)    # Adjust for the revision
    return config


@attr.s
class _Values():

    """Configuration data values."""

    product_rev = attr.ib(validator=attr.validators.instance_of(str))
    hardware_rev = attr.ib(validator=attr.validators.instance_of(str))
    sw_arm_image = attr.ib(validator=attr.validators.instance_of(str))
    sw_nrf_image = attr.ib(validator=attr.validators.instance_of(str))
    is_smartlink = attr.ib(validator=attr.validators.instance_of(bool))


class _Config():

    """Configuration options."""

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        try:
            rev = uut.lot.item.revision
        except AttributeError:
            rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        values = cls._rev_data[rev]
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.sw_arm_image = values.sw_arm_image
        cls.sw_nrf_image = values.sw_nrf_image
        cls.is_smartlink = values.is_smartlink


class BLExtender(_Config):

    """BLExtender config."""

    _arm_image = 'nxp_v0.1.0.bin'
    _hw_rev = '02B'
    _rev1_values = _Values(
        product_rev = '01A',
        hardware_rev = _hw_rev,
        sw_arm_image = _arm_image,      # no NXP in this product
        sw_nrf_image = (
            'blextender_v1.3.0-0-g6c6b4fa-signed-mcuboot-factory.hex'),
        is_smartlink = False
        )
    _rev_data = {
        None: _rev1_values,
        '1': _rev1_values,
        }


class SmartLink201(_Config):

    """SmartLink201 config."""

    _arm_image = 'nxp_v0.1.0.bin'
    _hw_rev = '02B'
    _rev3_values = _Values(
            product_rev = '03A',
            hardware_rev = _hw_rev,
            sw_arm_image = _arm_image,
            sw_nrf_image = (
                'smartlink_signed_1.1.7-0-g71f7a79_factory_mcuboot.hex'),
            is_smartlink = True
            )
    _rev_data = {
        None: _rev3_values,
        '3': _rev3_values,
        '2': _Values(
            product_rev = '02A',
            hardware_rev = _hw_rev,
            sw_arm_image = _arm_image,
            sw_nrf_image = (
                'smartlink_signed_1.0.0-0-gacbb530_factory_mcuboot.hex'),
            is_smartlink = True
            ),
        # No Rev 1 production
        }
