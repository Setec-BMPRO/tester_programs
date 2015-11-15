#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('5V', 1, 4.95, 5.05, None, None),
    ('SwRev', 1, 1.5, 2.5, None, None),
    ('MicroTemp', 1, 8.0, 30.0, None, None),
    ('5VOff', 1, 0.5, None, None, None),
    ('15VpOff', 1, 0.5, None, None, None),
    ('15VpSwOff', 1, 0.5, None, None, None),
    ('PwrGoodOff', 1, 0.5, None, None, None),
    ('20VL', 1, 18.0, 25.0, None, None),
    ('-20V', 1, -25.0, -18.0, None, None),
    ('15V', 1, 14.25, 15.75, None, None),
    ('-15V', 1, -15.75, -14.25, None, None),
    ('15Vp', 1, 14.25, 15.75, None, None),
    ('PwrGood', 1, 4.8, 5.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    )
