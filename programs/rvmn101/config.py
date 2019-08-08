#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Configuration."""

import tester


class Config():

    """Base configuration for RVMN101A/B."""

    #  Software version
    arm_image = 'rvmn101_nxp_1.9.bin'
    hardware_rev = None
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
    # Final Test limits common to both units
    _base_limits_final = (
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        tester.LimitBoolean('ScanMac', True,
            doc='MAC address detected'),
        tester.LimitHigh('ScanRSSI', -80,
            doc='Strong BLE signal'),
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

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final


class RVMN101A(Config):

    """RVMN101A configuration."""

    # Initial Test parameters
    fixture = '033550'
    #  Software version
    nordic_image = 'jayco_rvmn101_signed_1.3.3-0-g123e32e_factory_mcuboot.hex'
    product_rev = '06E'     # per PC-5077
    hardware_rev = '05D'    # per PC-5077


class RVMN101B(Config):

    """RVMN101B configuration."""

    # Initial Test parameters
    fixture = '032871'
    #  Software version
    nordic_image = 'tmc_rvmn101_signed_0.88-0-g5f64a82_factory_mcuboot'
    product_rev = '05B'     # per PC-5079
    hardware_rev = '05B'    # per PC-5079
