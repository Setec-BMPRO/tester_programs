#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""CN101 Configuration."""

import logging

import tester

import share


class CN101():

    """Configuration for CN101."""

    # Initial test limits
    limits_initial = (
            tester.LimitRegExp('SwVer', '',            # Adjusted during open()
                doc='Software version'),
            tester.LimitLow('Part', 100.0),
            tester.LimitDelta('Vin', 8.0, 0.5),
            tester.LimitPercent('3V3', 3.30, 3.0),
            tester.LimitInteger('CAN_BIND', 1 << 28),
            tester.LimitRegExp('BtMac', share.bluetooth.MAC.line_regex),
            tester.LimitBoolean('DetectBT', True),
            tester.LimitInteger('Tank', 5),
            )
    # MA-239: Upgrade all units to CN101T, so treat them as Rev 6
    _rev6_values = ('1.2.17835.298', (6, 0, 'A'), 2)     # CN101T (Rev 6)
    # Revision data dictionary
    _rev_data = {
        None: _rev6_values,
        6: _rev6_values,
        5: _rev6_values,
        4: _rev6_values,
        3: _rev6_values,
        2: _rev6_values,
        1: _rev6_values,
        }
    # These values get set per revision by select()
    sw_version = None
    hw_version = None
    banner_lines = None

    @classmethod
    def get(cls, uut):
        """Get configuration based on UUT Lot Number.

        @param uut setec.UUT instance
        @return configuration class

        """
        try:
            rev = uut.lot.item.revision
        except AttributeError:
            rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.sw_version, cls.hw_version, cls.banner_lines = cls._rev_data[rev]
        return cls
