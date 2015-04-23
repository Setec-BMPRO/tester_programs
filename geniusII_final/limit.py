#!/usr/bin/env python3
"""GENIUS-II and GENIUS-II-H Final Test Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('InRes', 1, 80000, 170000, None, None),
    ('Vout', 1, 13.575, 13.725, None, None),
    ('VoutOff', 1, -0.5, 2.0, None, None),
    ('VoutStartup', 1, 13.60, 14.10, None, None),
    ('Vbat', 1, 13.575, 13.725, None, None),
    ('VbatOff', 1, -0.5, 1, None, None),
    ('ExtBatt', 1, 11.5, 12.8, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('MaxBattLoad', 1, 15.0, None, None, None),
    ('Notify', 2, None, None, None, True),
    )

DATA_H = (
    ('InRes', 1, 80000, 170000, None, None),
    ('Vout', 1, 13.575, 13.725, None, None),
    ('VoutOff', 1, -0.5, 2.0, None, None),
    ('VoutStartup', 1, 13.60, 14.10, None, None),
    ('Vbat', 1, 13.575, 13.725, None, None),
    ('VbatOff', 1, -0.5, 1, None, None),
    ('ExtBatt', 1, 11.5, 12.8, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('MaxBattLoad', 1, 30.0, None, None, None),
    ('Notify', 2, None, None, None, True),
    )
