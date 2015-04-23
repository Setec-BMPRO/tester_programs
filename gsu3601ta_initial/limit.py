#!/usr/bin/env python3
"""GSU360-1TA Initial Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACin', 0, 85, 95, None, None),
    ('PFC', 1, 389.0, 415.0, None, None),
    ('PriCtl', 1, 12.0, 14.0, None, None),
    ('PriVref', 1, 7.3, 7.6, None, None),
    ('24Vnl', 1, 23.40, 24.60, None, None),
    ('24Vfl', 1, 23.32, 24.60, None, None),
    ('Fan12V', 1, 11.4, 12.6, None, None),
    ('SecCtl', 1, 22.0, 28.0, None, None),
    ('SecVref', 1, 2.4, 2.6, None, None),
    ('FixtureLock', 0, 0, 20, None, None),
    ('OCP', 1, 15.2, 21.0, None, None),
    ('inOCP', 1, 23.0, None, None, None),
    )
