#!/usr/bin/env python3
"""2040 Initial Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('VccAC', 1, 9.0, 16.5, None, None),
    ('VccDC', 1, 7.8, 14.0, None, None),
    ('VbusMin', 1, 120.0, 140.0, None, None),
    ('SDOff', 1, 19.0, 21.0, None, None),
    ('SDOn', 1, 5.0, None, None, None),
    ('ACmin', 1, 88.0, 92.0, None, None),
    ('ACtyp', 1, 238.0, 242.0, None, None),
    ('ACmax', 1, 263.0, 267.0, None, None),
    ('VoutExt', 1, 19.8, 20.2, None, None),
    ('Vout', 1, 19.6, 20.4, None, None),
    ('GreenOn', 1, 15.0, 20.0, None, None),
    ('RedDCOff', 1, 9.0, 15.0, None, None),
    ('RedDCOn', 1, 1.8, 3.5, None, None),
    ('RedACOff', 1, 9.0, 50.0, None, None),
    ('DCmin', 1, 9.0, 11.0, None, None),
    ('DCtyp', 1, 23.0, 26.0, None, None),
    ('DCmax', 1, 38.0, 42.0, None, None),
    ('OCP', 1, 3.5, 4.1, None, None),
    ('inOCP', 1, 19.0, None, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Notify', 2, None, None, None, True),
    )
