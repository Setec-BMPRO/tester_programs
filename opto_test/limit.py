#!/usr/bin/env python3
"""Opto Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    # Set 0.005 back from 1mA.
    ('Isen', 1, None, 0.995, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    # 1mA +/- 1%.
    ('Iin', 1, 0.990, 1.01, None, None),
    # Set 0.02 back from -5.0V.
    ('Vsen', 1, -4.98, None, None, None),
    # -5.0V +/- 1%.
    ('Vce', 1, -5.05, -4.95, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0.0, 1.0, None, None),
    ('CTR', 1, 0, 100, None, None),
    )
