#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Final Test Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('InRes', 1, 60000, 80000, None, None),
    ('IECoff', 1, 0.5, None, None, None),
    ('IEC', 1, 235, 245, None, None),
    ('5V', 1, 5.034, 5.177, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 12.005, 12.495, None, None),
    ('24Von', 1, 23.647, 24.613, None, None),
    ('5Vfl', 1, 4.820, 5.380, None, None),
    ('12Vfl', 1, 11.270, 13.230, None, None),
    ('24Vfl', 1, 21.596, 26.663, None, None),
    ('PwrGood', 1, 0.5, None, None, None),
    ('AcFail', 1, 4.5, 5.5, None, None),
    ('Reg12V', 1, 0.5, 5.0, None, None),
    ('Reg24V', 1, 0.2, 5.0, None, None),
    ('Notify', 2, None, None, None, True),
    )
