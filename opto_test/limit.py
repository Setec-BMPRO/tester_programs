#!/usr/bin/env python3
"""Opto Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    # Set 0.005 back from 1mA.
    ('Isen1', 1, None, 0.995, None, None),
    # Set 0.05 back from 10mA.
    ('Isen10', 1, None, 9.95, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    # 1mA +/- 1%.
    ('Iin1', 1, 0.99, 1.01, None, None),
    # 10mA +/- 1%.
    ('Iin10', 1, 9.9, 10.1, None, None),
    # Set 0.02 back from -5.0V.
    ('Vsen', 1, -4.98, None, None, None),
    # -5.0V +/- 1%.
    ('Vce', 1, -5.05, -4.95, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0.0, 10.0, None, None),
    ('CTR', 1, 0, 100, None, None),
    ('SerNum', 0, None, None, r'^A[0-9]{4}$', None),
    )
