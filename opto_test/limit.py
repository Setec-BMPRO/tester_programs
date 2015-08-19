#!/usr/bin/env python3
"""Opto Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Isen', 1, None, 0.99, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    ('Iin', 1, 1.0, 1.01, None, None),
    ('Vsen', 1, -4.99, None, None, None),
    ('Vce', 1, -5.25, -5.0, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0.2, 1.2, None, None),
    ('CTR', 1, 50, 120, None, None),
    )
