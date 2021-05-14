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
    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Rev 1-4: No Production
# MA-239: Upgrade all units to CN101T, so treat them as Rev 6
#        (share.lots.Range('A164207', 'A182702'), 5),    # 029431
        # Rev 6... Rev 5 units built as Rev 6 under PC
        ))
    # Revision data dictionary
    _rev_data = {
        None: ('1.2.17835.298', (6, 0, 'A'), 2),         # CN101T (Rev 6)
# MA-239: Upgrade all units to CN101T, so treat them as Rev 6
#        5: ('1.1.13665.176', (5, 0, 'A'), 0),            # CN101 (Rev 1-5)
        }
    # These values get set per revision by select()
    sw_version = None
    hw_version = None
    banner_lines = None

    @classmethod
    def select(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance
        @return configuration class

        """
        rev = None
        if uut:
            try:
                rev = cls._lot_rev.find(uut.lot.number)
            except share.lots.LotError:
                pass
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.sw_version, cls.hw_version, cls.banner_lines = cls._rev_data[rev]
        return cls
