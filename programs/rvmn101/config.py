#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Configuration."""

import tester


class Config():

    """Base configuration for RVMN101A/B."""

    # General parameters used in testing the units
    #  Injected voltages
    vbatt_set = 12.5
    # Initial Test limits common to both units
    _base_limits_initial = (
        tester.LimitDelta('Vbatt', vbatt_set - 0.5, 0.5, doc='Battery input'),
        tester.LimitPercent('3V3', 3.3, 6.0, doc='Internal 3V rail'),
        tester.LimitLow('HSoff', 1.0, doc='All HS outputs off'),
        tester.LimitHigh('HSon', 10.0, doc='HS output on'),
        tester.LimitHigh('LSoff', 10.0, doc='LS output off'),
        tester.LimitLow('LSon', 1.0, doc='LS output on'),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )

    @staticmethod
    def get(parameter):
        """Select a configuration based on the parameter.

        @param parameter Type of unit (A/B)
        @return configuration class

        """
        return {'A': RVMN101A, 'B': RVMN101B}[parameter]

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_initial


class RVMN101A(Config):

    """RVMN101A configuration."""

    # Initial Test parameters
    fixture = '033550'
    #  Software version
# FIXME: We need software images
    arm_image = None
    nordic_image = None
    # Product revision per PC-5052
    product_rev = None


class RVMN101B(Config):

    """RVMN101B configuration."""

    # Initial Test parameters
    fixture = '032871'
    #  Software version
    arm_image = 'rvmn101b_nxp_1.9.bin'
    nordic_image = 'rvmn101_signed_0.74-0-g5d7a6d1_factory_mcuboot.hex'
    # Product revision per PC-5052
    product_rev = '04E'
