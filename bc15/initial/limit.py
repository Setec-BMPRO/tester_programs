#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACin', 0, 235.0, 245.0, None, None),
    ('Vbus', 0, 325.0, 345.0, None, None),
    ('14Vpri', 0, 13.0, 15.0, None, None),
    ('12Vs', 0, 11.7, 13.0, None, None),
    ('5Vs', 0, 4.9, 5.1, None, None),
    ('3V3', 0, 3.20, 3.35, None, None),
    ('FanOn', 0, 0.5, None, None, None),
    ('FanOff', 0, None, 11.0, None, None),
    ('15Vs', 0, 14.5, 16.5, None, None),
    ('Vout', 0, 14.3, 14.5, None, None),
    ('VoutOff', 0, 2.0, None, None, None),
    ('OCP', 0, 32.0, 35.1, None, None),
    ('InOCP', 0, 11.6, None, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('FanShort', 0, None, 100, None, None),
    ('Notify', 1, None, None, None, True),
    # Data reported by the ARM
    ('ARM-SwVer', 0, None, None, r'^1\.0\.11778\.1230$', None),
    )
