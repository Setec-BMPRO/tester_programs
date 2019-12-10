#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 SETEC Pty Ltd
"""CN102/3 Configuration."""

import collections
import logging

import tester
import share


class CN10x():

    """Configuration for CN10x."""

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
    # These values get overriden by child classes
    _lot_rev = None
    _rev_data = None
    # Adjustable configuration data values
    values = collections.namedtuple(
        'values',
        'sw_arm_version, sw_nrf_version, hw_version, banner_lines'
        )
    # These values get set per revision
    sw_arm_version = None
    sw_nrf_version = None
    hw_version = None
    banner_lines = None

    @classmethod
    def select(cls, parameter, uut):
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
        return config

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
        (cls.sw_arm_version, cls.sw_nrf_version,
         cls.hw_version, cls.banner_lines) = cls._rev_data[rev]


class CN102(CN10x):

    """Configuration for CN102."""

    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Default to None == Rev 1
        ))
    # Revision data dictionary:
    _rev_data = {
        None: CN10x.values(
            sw_arm_version='1.2.18218.1627',
            sw_nrf_version='1.0.18106.1260',
            hw_version=(1, 0, 'A'),
            banner_lines=2
            ),
        }


class CN103(CN10x):

    """Configuration for CN103."""

    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Default to None == Rev 1
        ))
    # Revision data dictionary:
    _rev_data = {
        None: CN10x.values(
#TODO: Fill in CN103 firmware versions
            sw_arm_version='xxxx',
            sw_nrf_version='yyyy',
            hw_version=(1, 0, 'A'),
            banner_lines=2
            ),
        }
