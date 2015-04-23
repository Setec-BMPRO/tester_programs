#!/usr/bin/env python3
"""SX-750 Safety Test Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('gnd', 0, 20, 100, None, None),
    ('arc', 0, -0.001, 0, None, None),
    ('acw', 0, 2.0, 4.0, None, None),
    )
