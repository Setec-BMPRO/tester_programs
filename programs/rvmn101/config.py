#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Configuration.

Bluetooth signal strength measurements:

    RaspberryPi @ATE2a tester
    Unit under Test:
    @ATE4a      Ant     -72db to -78db
                No-Ant  -100db to -95db
    @ ATE2a     Ant     -45db to -55db
                No-Ant  -85db - -92db

"""

import tester


class Config():

    """Base configuration for RVMN101A/B."""

    #  Software version
    arm_image = 'rvmn101_nxp_1.9.bin'
    hardware_rev = None
    # General parameters used in testing the units
    #  Injected voltages
    vbatt_set = 12.5
    # Test limits common to both units and test types
    _base_limits = (
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )
    # Initial Test limits common to both units
    _base_limits_initial = _base_limits + (
        tester.LimitDelta('Vbatt', vbatt_set - 0.5, 0.5, doc='Battery input'),
        tester.LimitPercent('3V3', 3.3, 6.0, doc='Internal 3V rail'),
        tester.LimitLow('HSoff', 1.0, doc='All HS outputs off'),
        tester.LimitHigh('HSon', 10.0, doc='HS output on'),
        tester.LimitHigh('LSoff', 10.0, doc='LS output off'),
        tester.LimitLow('LSon', 1.0, doc='LS output on'),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )
    # Final Test limits common to both units
    _base_limits_final = _base_limits + (
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        tester.LimitHigh('ScanRSSI', -80, doc='Strong BLE signal'),
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
    product_rev = '07A'
    hardware_rev = '07A'

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', -80, doc='Strong BLE signal'),
            )


class RVMN101B(Config):

    """RVMN101B configuration."""

    # Initial Test parameters
    fixture = '032871'
    #  Software version
    nordic_image = 'tmc_rvmn101_signed_0.88-0-g5f64a82_factory_mcuboot.hex'
    product_rev = '05B'     # per PC-5079
    hardware_rev = None     # Firmware 0.88 does not support hardware_rev

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', -100, doc='Strong BLE signal'),
            )
