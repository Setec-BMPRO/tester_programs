#!/usr/bin/env python3
"""Opto Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Iin', 1, None, 1.0, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    ('Isen', 1, 0, 99999, None, None),
    ('Vce', 1, -5.0, None, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0, 99999, None, None),
    ('CTR', 1, 50, 150, None, None),
    ('Notify', 2, None, None, None, True),
    )
