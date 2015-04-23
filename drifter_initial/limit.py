#!/usr/bin/env python3
"""Drifter(BM) Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
_COMMON = (
    ('Vin', 0, 11.9, 12.1, None, None),
    ('Vsw', 0, -100, 100, None, None),
    ('Vref', 0, -100, 100, None, None),
    ('Vcc', 0, 3.23, 3.37, None, None),
    ('Isense', 0, -95, -85, None, None),
    ('3V3', 0, -2.8, -2.5, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('%ErrorV', 0, -2.24, 2.24, None, None),
    ('%CalV', 0, -0.36, 0.36, None, None),
    ('%ErrorI', 0, -2.15, 2.15, None, None),
    ('%CalI', 0, -0.50, 0.50, None, None),
    # Data reported by the PIC
    ('Status 0', 0, -0.1, 0.1, None, None),
    ('ZeroChk', 0, -65.0, 65.0, None, None),
    ('PicVin', 0, 11.5, 12.5, None, None),
    ('PicIsense', 0, -95, -85, None, None),
    ('Vfactor', 0, 19000, 21000, None, None),
    ('Ifactor', 0, 14000, 16000, None, None),
    ('Ioffset', 0, -8.01, -8, None, None),
    ('Ithreshold', 0, 160, 160.01, None, None),
    )

DATA = _COMMON + (
    ('Software', 0, None, None, 'Drifter-5.hex', None),
    ('0V8', 0, -1.2, -0.4, None, None),
    )

DATA_BM = _COMMON + (
    ('Software', 0, None, None, 'DrifterBM-2.hex', None),
    ('0V8', 0, -1.4, -0.6, None, None),
    )
