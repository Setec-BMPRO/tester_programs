#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN102 Configuration."""

import logging
from tester import (
    LimitLow, LimitDelta, LimitPercent, LimitInteger,
    LimitRegExp, LimitBoolean,
    )
import share


class CN102():

    """Configuration for CN102."""

    # Initial test limits
    limits_initial = (
            LimitRegExp('SwArmVer', '',            # Adjusted during open()
                doc='ARM Software version'),
            LimitRegExp('SwNrfVer', '',            # Adjusted during open()
                doc='Nordic Software version'),
            LimitLow('Part', 20.0),
            LimitDelta('Vin', 8.0, 0.5),
            LimitPercent('3V3', 3.30, 3.0),
            LimitInteger('CAN_BIND', 1 << 28),
            LimitBoolean('ScanSer', True, doc='Serial number detected'),
            LimitInteger('Tank', 5),
            )
    # Lot Number to Revision data
    _lot_rev = share.lots.Revision((
        # Rev 1...
        ))
    # Revision data dictionary
    _rev_data = {
        None: ('1.2.18218.1627', '1.0.18106.1260', (1, 0, 'A'), 2),
        }
    # These values get set per revision by select()
    sw_arm_version = None
    sw_nrf_version = None
    hw_version = None
    banner_lines = None

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
        (cls.sw_arm_version, cls.sw_nrf_version,
         cls.hw_version, cls.banner_lines) = cls._rev_data[rev]
        return cls
