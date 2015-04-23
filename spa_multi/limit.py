#!/usr/bin/env python3
"""Spa RGB/TRI Test Program Limits."""

# Test Limits for RGB
#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA_RGB = (
    ('AcVin10', 0, 10.4, 10.6, None, None),
    ('AcIin10', 0, 0.10, 0.50, None, None),
    ('AcVin12', 0, 11.9, 12.1, None, None),
    ('AcIin12', 0, 0.10, 0.50, None, None),
    ('AcVin24', 0, 23.9, 24.1, None, None),
    ('AcIin24', 0, 0.10, 0.50, None, None),
    ('AcVin32', 0, 31.9, 32.1, None, None),
    ('AcIin32', 0, 0.10, 0.50, None, None),
    ('AcVin35', 0, 34.9, 35.1, None, None),
    ('AcIin35', 0, 0.10, 0.50, None, None),
    ('Vcc', 0, 3.30, 3.90, None, None),
#    ('Iled10', 0, 0.65, 0.88, None, None),
    ('Iled10', 0, 0.265, 0.88, None, None),
#    ('Iled', 0, 0.72, 0.88, None, None),
    ('Iled', 0, 0.472, 0.88, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('HexRGB', 0, None, None, 'MFDrgb_V103.hex', None),
    ('HexTRI', 0, None, None, 'MFDtri_V103.hex', None),
    )

# Test Limits for TRI
DATA_TRI = DATA_RGB
