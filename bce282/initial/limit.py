#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA12 = (
        ('VccBiasExt', 1, 14.0, 16.0, None, None),
        ('Vac', 1, 235.0, 245.0, None, None),
        ('Vbus', 1, 330.0, 350.0, None, None),
        # 15.60 +/- 5%
        ('VccPri', 1, 14.82, 16.38, None, None),
        # 15.0 +/ 13%
        ('VccBias', 1, 13.05, 16.95, None, None),
        ('VbatOff', 1, 0.5, None, None, None),
        ('AlarmClosed', 1, 1000, 3000, None, None),
        ('AlarmOpen', 1, 11000, 13000, None, None),
        ('FullLoad', 1, 20.1, None, None, None),
        ('BattOCPramp', 1, 14.0, 16.0, None, None),
        ('BattOCP', 1, 14.175, 15.825, None, None),
        ('OutOCPramp', 1, 19.5, 25.0, None, None),
        ('OutOCP', 1, 20.05, 24.00, None, None),
        ('inOCP', 1, 13.0, None, None, None),
        ('FixtureLock', 0, 20, None, None, None),
        # 13.8 +/- 2.6%
        ('VoutPreCal', 1, 13.4412, 14.1588, None, None),
        # Data reported by the MSP430
        ('Status 0', 0, -0.1, 0.1, None, None),
        ('MspVout', 0, 13.0, 14.6, None, None),
        )

DATA24 = (
        ('VccBiasExt', 1, 14.0, 16.0, None, None),
        ('Vac', 1, 235.0, 245.0, None, None),
        ('Vbus', 1, 330.0, 350.0, None, None),
        # 15.60 +/- 5%
        ('VccPri', 1, 14.82, 16.38, None, None),
        # 15.0 +/ 13%
        ('VccBias', 1, 13.05, 16.95, None, None),
        ('VbatOff', 1, 0.5, None, None, None),
        ('AlarmClosed', 1, 1000, 3000, None, None),
        ('AlarmOpen', 1, 11000, 13000, None, None),
        ('FullLoad', 1, 10.1, None, None, None),
        ('BattOCPramp', 1, 5.5, 9.5, None, None),
        ('BattOCP', 1, 6.0, 9.0, None, None),
        ('OutOCPramp', 1, 9.5, 12.5, None, None),
        ('OutOCP', 1, 10.0, 12.0, None, None),
        ('inOCP', 1, 26.0, None, None, None),
        ('FixtureLock', 0, 20, None, None, None),
        # 27.5 +/- 2.6%
        ('VoutPreCal', 1, 26.785, 28.215, None, None),
        # Data reported by the MSP430
        ('Status 0', 0, -0.1, 0.1, None, None),
        ('MspVout', 0, 13.0, 14.6, None, None),
        )
