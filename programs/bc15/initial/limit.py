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
    ('Vout', 0, 14.40 * 0.95, 14.40 * 1.05, None, None),
    ('VoutCal', 0, 14.40 * 0.99, 14.40 * 1.01, None, None),
    ('VoutOff', 0, 2.0, None, None, None),
    ('OCP', 0, 15.0 * 0.95, 15.0 * 1.05, None, None),
    ('InOCP', 0, 12.0, None, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('FanShort', 0, None, 100, None, None),
    # Data reported by the ARM
    ('ARM-SwVer', 0, None, None, r'^1\.0\.11881\.1274$', None),
    ('ARM-Vout', 0, 14.40 * 0.95, 14.40 * 1.05, None, None),
    ('ARM-2amp', 0, 0.5, 3.5, None, None),
    # Why 'Lucky'?
    #   The circuit specs are +/- 1.5A, and we hope to be lucky
    #   and get units within +/- 1.0A ...
    ('ARM-2amp-Lucky', 0, 1.0, 3.0, None, None),
    ('ARM-14amp', 0, 12.0, 16.0, None, None),
    ('ARM-switch', 0, 2.5, 3.5, None, None),
    )