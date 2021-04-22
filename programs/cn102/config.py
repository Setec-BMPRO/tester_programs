#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""CN102/3 Configuration."""

import logging

import tester
import share


class CN10xParameters():

    """CN10x model specific parameters."""

    # Initial test limits
    limits_initial = (
        tester.LimitRegExp('SwArmVer', '',      # Adjusted during open()
            doc='ARM Software version'),
        tester.LimitRegExp('SwNrfVer', '',      # Adjusted during open()
            doc='Nordic Software version'),
        tester.LimitLow('Part', 500.0),
        tester.LimitDelta('Vin', 8.0, 0.5),
        tester.LimitPercent('3V3', 3.30, 3.0),
        tester.LimitInteger('CAN_BIND', 1 << 28),
        tester.LimitBoolean('ScanSer', True,
            doc='Serial number detected'),
        tester.LimitInteger('Tank', 5),
        )

    # Final test limits
    limits_final = (
        tester.LimitHigh(
            'ScanRSSI',
            -70 if share.config.System.tester_type in (
                'ATE4', 'ATE5') else -85,
            doc='Strong BLE signal'),
        )

    def __init__(self,
            prefix,
            sw_arm_version, sw_nrf_version,
            hw_version, banner_lines):
        """Create instance.

        @param prefix Filename prefix ('cn102' or 'cn103')
        @param sw_arm_version ARM (NXP) version
        @param sw_nrf_version Nordic version
        @param hw_version Hardware version
        @param banner_lines Number of startup banner lines

        """
        self.sw_arm_version = sw_arm_version
        self.sw_arm_image = '{0}_arm_{1}.bin'.format(
            prefix, sw_arm_version)
        self.sw_nrf_version = sw_nrf_version
        self.sw_nrf_image = '{0}_nrf_{1}.hex'.format(
            prefix, sw_nrf_version)
        self.hw_version = hw_version
        self.banner_lines = banner_lines


class CN10x():

    """Configuration for CN10x."""

    # These values get overriden by child classes
    _lot_rev = None
    _rev_data = None
    # Instance of CN10xParameters
    parameters = None

    @classmethod
    def get(cls, parameter, uut):
        """Adjust configuration based on UUT Lot Number.

        @param parameter Type of unit (A/B/C)
        @param uut storage.UUT instance
        @return configuration class

        """
        config = {
            '102': CN102,
            '103': CN103,
            }[parameter]
        config._configure(uut)    # Adjust for the Lot Number
        return config.parameters

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut storage.UUT instance

        """
        rev = None
        if uut:
            lot = uut.lot
            try:
                rev = cls._lot_rev.find(lot)
            except share.lots.LotError:
                pass
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.parameters = cls._rev_data[rev]


class CN102(CN10x):

    """Configuration for CN102."""

    _prefix = 'cn102'
    # Software versions
    _arm_12 = '1.2.18218.1627'
    _nordic_10 = '1.0.18106.1260'
    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Default to None == Rev 1
        ))
    # Revision data dictionary:
    _rev_data = {
        None: CN10xParameters(
            prefix=_prefix,
            sw_arm_version=_arm_12,
            sw_nrf_version=_nordic_10,
            hw_version=(1, 0, 'A'),
            banner_lines=2
            ),
        }


class CN103(CN10x):

    """Configuration for CN103."""

    _prefix = 'cn103'
    # Software versions
    _arm_12 = '1.2.111.2008'
    _nordic_10 = '1.0.19700.1352'
    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Rev 1
        (share.lots.Range('A195014', 'A200419'), 1),
        # Rev 2...
        ))
    # Revision data dictionary:
    _rev_data = {
        None: CN10xParameters(
            prefix=_prefix,
            sw_arm_version=_arm_12,
            sw_nrf_version=_nordic_10,
            hw_version=(2, 0, 'A'),
            banner_lines=2
            ),
        1: CN10xParameters(
            prefix=_prefix,
            sw_arm_version=_arm_12,
            sw_nrf_version=_nordic_10,
            hw_version=(1, 0, 'A'),
            banner_lines=2
            ),
        }
