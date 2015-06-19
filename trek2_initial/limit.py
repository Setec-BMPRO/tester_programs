#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
        ('Vin', 1, 11.5, 12.5, None, None),
        # 3.3 +/- 3%
        ('3V3', 1, 3.25, 3.35, None, None),
        ('BkLghtOff', 1, 11.5, 12.5, None, None),
        ('BkLghtOn', 1, 0.5, None, None, None),
        ('Program', 2, -0.1, 0.1, None, None),
        ('Notify', 2, None, None, None, True),
        )
