#!/usr/bin/env python3
"""Opto Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Isen', 1, None, 1.0, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    ('Iin', 1, 0.9, 1.1, None, None),
    ('Vce', 1, -5.0, None, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0.2, 1.5, None, None),
    ('CTR', 1, 30, 150, None, None),
    )
