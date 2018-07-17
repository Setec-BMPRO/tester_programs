#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Configuration."""

import logging
from tester import (
    LimitLow, LimitDelta, LimitPercent, LimitInteger,
    LimitRegExp, LimitBoolean,
    )
import share


class CN101():

    """Configuration for CN101."""

    # Initial test limits
    limits_initial = (
            LimitRegExp('SwVer', '', doc='Software version'),
            LimitLow('Part', 20.0),
            LimitDelta('Vin', 8.0, 0.5),
            LimitPercent('3V3', 3.30, 3.0),
            LimitInteger('CAN_BIND', 1 << 28),
            LimitRegExp('BtMac', share.bluetooth.MAC.line_regex),
            LimitBoolean('DetectBT', True),
            LimitInteger('Tank', 5),
            )
    # Available software versions
    sw_12 = '1.2.17835.298'     # CN101T (Rev 6)
    sw_11 = '1.1.13665.176'     # CN101 (Rev 1-5)
    # These values get set per revision
    sw_version = None
    hw_version = None
    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Rev 1-4: No Production
        (share.lots.Range('A000000', 'A182702'), 5),    # 029431
        # Rev 6...                                      # 031968
        ))
    # Revision data dictionary
    _rev_data = {
        None: (sw_12, (6, 0, 'A'), ),
        5: (sw_11, (5, 0, 'A'), ),
        }

    @classmethod
    def select(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut storage.UUT instance
        @return configuration class

        """
        rev = None
        if uut:
            lot = uut.lot
            try:
                rev = cls._lot_rev.find(lot)
            except share.lots.LotError:
                pass
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.sw_version, cls.hw_version = cls._rev_data[rev]
        return cls
